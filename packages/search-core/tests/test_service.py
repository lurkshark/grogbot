from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import urlparse

import httpx
import pysqlite3 as sqlite3
import pytest

import grogbot_search.service as service_module
from grogbot_search.models import Document
from grogbot_search.service import BackoffError, DocumentNotFoundError, SearchService


def _chunk_texts(service: SearchService, document_id: str) -> list[str]:
    rows = service.connection.execute(
        "SELECT content_text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document_id,),
    ).fetchall()
    return [row["content_text"] for row in rows]


# Core source/document/chunk persistence behavior

def test_source_upsert_and_cascade_delete(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello",
        published_at=None,
        content_markdown="Hello world",
    )

    assert service.delete_source(source.id) is True
    assert service.get_document(document.id) is None
    chunk_count = service.connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
    assert chunk_count == 0


def test_document_upsert_regenerates_chunks(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello",
        published_at=None,
        content_markdown="Hello world",
    )
    service.embed_document_chunks(document.id)
    initial_chunks = _chunk_texts(service, document.id)

    updated = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello again",
        published_at=None,
        content_markdown="Hello world updated content",
    )
    updated_chunks = _chunk_texts(service, updated.id)

    assert initial_chunks != updated_chunks
    vector_rows = service.connection.execute(
        "SELECT COUNT(*) AS count FROM chunks_vec",
    ).fetchone()
    assert vector_rows["count"] == 0


def test_upsert_document_without_content_change_preserves_existing_chunks(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/stable",
        title="Stable",
        published_at=None,
        content_markdown="stable body",
    )
    service.embed_document_chunks(document.id)

    original_chunk_rows = service.connection.execute(
        "SELECT id, content_text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document.id,),
    ).fetchall()

    updated = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/stable",
        title="Stable (renamed)",
        published_at=None,
        content_markdown="stable body",
    )

    assert updated.id == document.id
    assert updated.title == "Stable (renamed)"

    updated_chunk_rows = service.connection.execute(
        "SELECT id, content_text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document.id,),
    ).fetchall()
    assert [(row["id"], row["content_text"]) for row in updated_chunk_rows] == [
        (row["id"], row["content_text"]) for row in original_chunk_rows
    ]


def test_upsert_document_without_content_change_preserves_existing_links(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/stable-links",
        title="Stable Links",
        published_at=None,
        content_markdown="[other](https://other.example/target)",
    )

    original_links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ?",
        (document.id,),
    ).fetchall()
    original_hash = document.content_hash

    updated = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/stable-links",
        title="Stable Links (renamed)",
        published_at=None,
        content_markdown="[other](https://other.example/target)",
    )

    updated_links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ?",
        (updated.id,),
    ).fetchall()
    assert updated.content_hash == original_hash
    assert [row["to_document_id"] for row in updated_links] == [row["to_document_id"] for row in original_links]


def test_upsert_document_chunks_inline_heading_context(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/context",
        title="Context",
        published_at=None,
        content_markdown="""# API

## Auth

token details
""",
    )

    assert _chunk_texts(service, document.id) == ["API > Auth token details"]


def test_upsert_document_rejects_empty_content(service: SearchService):
    source = service.upsert_source("example.com", name="Example")

    with pytest.raises(ValueError):
        service.upsert_document(
            source_id=source.id,
            canonical_url="https://example.com/empty",
            title="Empty",
            published_at=None,
            content_markdown="   ",
        )

    doc_count = service.connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
    assert doc_count == 0


def test_documents_table_enforces_content_hash_shape(service: SearchService):
    source = service.upsert_source("example.com", name="Example")

    with pytest.raises(sqlite3.IntegrityError):
        service.connection.execute(
            """
            INSERT INTO documents (id, source_id, canonical_url, title, published_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "doc-invalid-hash",
                source.id,
                "https://example.com/invalid-hash",
                "Invalid hash",
                None,
                "ABC123",
            ),
        )


def test_delete_document_cascades_chunks_and_vector_rows(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/deletable",
        title="Delete Me",
        published_at=None,
        content_markdown="alpha beta gamma",
    )
    service.embed_document_chunks(document.id)

    assert service.delete_document(document.id) is True
    assert service.delete_document(document.id) is False

    chunk_rows = service.connection.execute(
        "SELECT COUNT(*) AS count FROM chunks WHERE document_id = ?",
        (document.id,),
    ).fetchone()
    assert chunk_rows["count"] == 0
    total_vector_rows = service.connection.execute("SELECT COUNT(*) AS count FROM chunks_vec").fetchone()
    assert total_vector_rows["count"] == 0


def test_list_documents_can_filter_by_source(service: SearchService):
    source_a = service.upsert_source("a.example", name="A")
    source_b = service.upsert_source("b.example", name="B")

    doc_a = service.upsert_document(
        source_id=source_a.id,
        canonical_url="https://a.example/one",
        title="One",
        published_at=None,
        content_markdown="alpha",
    )
    service.upsert_document(
        source_id=source_b.id,
        canonical_url="https://b.example/two",
        title="Two",
        published_at=None,
        content_markdown="beta",
    )

    filtered = service.list_documents(source_id=source_a.id)

    assert [document.id for document in filtered] == [doc_a.id]


def test_statistics_global_and_source_scoped(service: SearchService):
    source_a = service.upsert_source("alpha.example", name="Alpha")
    source_b = service.upsert_source("beta.example", name="Beta")

    service.upsert_document(
        source_id=source_a.id,
        canonical_url="https://alpha.example/doc-1",
        title="Doc 1",
        published_at=None,
        content_markdown="alpha",
    )
    doc_a2 = service.upsert_document(
        source_id=source_a.id,
        canonical_url="https://alpha.example/doc-2",
        title="Doc 2",
        published_at=None,
        content_markdown="alpha [link](https://external.example/one)",
    )
    doc_b1 = service.upsert_document(
        source_id=source_b.id,
        canonical_url="https://beta.example/doc-1",
        title="Doc B1",
        published_at=None,
        content_markdown="beta [link](https://external.example/two)",
    )

    service.embed_document_chunks(doc_a2.id)
    service.embed_document_chunks(doc_b1.id)

    stats = service.statistics()

    assert stats.total_sources == 2
    assert stats.total_documents == 3
    assert stats.total_chunks == 3
    assert stats.total_links == 2
    assert stats.embedded_chunks == 2
    assert stats.embedding_progress == pytest.approx(2 / 3 * 100.0)
    assert stats.avg_chunks_per_document == pytest.approx(1.0)
    assert stats.avg_documents_per_source == pytest.approx(1.5)

    source_stats = service.statistics(source_id=source_a.id)

    assert source_stats.total_sources == 1
    assert source_stats.total_documents == 2
    assert source_stats.total_chunks == 2
    assert source_stats.total_links == 1
    assert source_stats.embedded_chunks == 1
    assert source_stats.embedding_progress == pytest.approx(50.0)
    assert source_stats.avg_chunks_per_document == pytest.approx(1.0)
    assert source_stats.avg_documents_per_source == pytest.approx(2.0)


def test_statistics_empty_dataset_returns_zero(service: SearchService):
    stats = service.statistics()

    assert stats.total_sources == 0
    assert stats.total_documents == 0
    assert stats.total_chunks == 0
    assert stats.total_links == 0
    assert stats.embedded_chunks == 0
    assert stats.embedding_progress == 0.0
    assert stats.avg_chunks_per_document == 0.0
    assert stats.avg_documents_per_source == 0.0


def test_statistics_missing_source_returns_zero(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/one",
        title="One",
        published_at=None,
        content_markdown="alpha",
    )

    stats = service.statistics(source_id="missing-source")

    assert stats.total_sources == 0
    assert stats.total_documents == 0
    assert stats.total_chunks == 0
    assert stats.total_links == 0
    assert stats.embedded_chunks == 0
    assert stats.embedding_progress == 0.0
    assert stats.avg_chunks_per_document == 0.0
    assert stats.avg_documents_per_source == 0.0


def test_embed_document_chunks_returns_count(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/chunk",
        title="Chunk",
        published_at=None,
        content_markdown="Hello world",
    )

    created = service.embed_document_chunks(document.id)

    row = service.connection.execute(
        "SELECT COUNT(*) AS count FROM chunks WHERE document_id = ?",
        (document.id,),
    ).fetchone()
    assert created == row["count"]
    assert created > 0


def test_embed_document_chunks_missing_raises(service: SearchService):
    with pytest.raises(DocumentNotFoundError):
        service.embed_document_chunks("missing-id")


def test_synchronize_document_embeddings_respects_maximum(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/first",
        title="First",
        published_at=None,
        content_markdown="first content",
    )
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/second",
        title="Second",
        published_at=None,
        content_markdown="second content",
    )

    created = service.synchronize_document_embeddings(maximum=1)
    embedded_docs = service.connection.execute(
        """
        SELECT DISTINCT chunks.document_id
        FROM chunks
        JOIN chunks_vec ON chunks_vec.rowid = chunks.id
        ORDER BY chunks.document_id
        """
    ).fetchall()
    assert len(embedded_docs) == 1
    assert created > 0

    service.synchronize_document_embeddings()
    embedded_docs = service.connection.execute(
        """
        SELECT DISTINCT chunks.document_id
        FROM chunks
        JOIN chunks_vec ON chunks_vec.rowid = chunks.id
        ORDER BY chunks.document_id
        """
    ).fetchall()
    assert len(embedded_docs) == 2


def test_synchronize_document_embeddings_non_positive_maximum_is_noop(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/noop",
        title="Noop",
        published_at=None,
        content_markdown="noop",
    )

    assert service.synchronize_document_embeddings(maximum=0) == 0
    assert service.synchronize_document_embeddings(maximum=-5) == 0
    vector_count = service.connection.execute("SELECT COUNT(*) AS count FROM chunks_vec").fetchone()["count"]
    assert vector_count == 0


# Link graph behavior

def test_embed_document_chunks_skips_same_domain_links_and_dedupes_cross_domain_targets(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/source",
        title="Source",
        published_at=None,
        content_markdown=(
            "[same](https://example.com/target) "
            "[cross-one](https://other.example/target) "
            "[cross-one-duplicate](https://other.example/target) "
            "[cross-two](https://third.example/other-target)"
        ),
    )

    service.embed_document_chunks(document.id)

    links = service.connection.execute(
        """
        SELECT from_document_id, to_document_id
        FROM links
        WHERE from_document_id = ?
        ORDER BY to_document_id
        """,
        (document.id,),
    ).fetchall()

    assert len(links) == 2
    assert [row["to_document_id"] for row in links] == sorted(
        [
            service_module.document_id_for_url(service_module._canonicalize_url("https://other.example/target")),
            service_module.document_id_for_url(service_module._canonicalize_url("https://third.example/other-target")),
        ]
    )


def test_embed_document_chunks_resolves_relative_links_before_domain_filtering(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/posts/entry",
        title="Entry",
        published_at=None,
        content_markdown=(
            "[root](/about) "
            "[parent](../archive) "
            "[cross](https://external.example/outbound)"
        ),
    )

    service.embed_document_chunks(document.id)

    links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ? ORDER BY to_document_id",
        (document.id,),
    ).fetchall()

    assert [row["to_document_id"] for row in links] == [
        service_module.document_id_for_url(service_module._canonicalize_url("https://external.example/outbound"))
    ]


def test_embed_document_chunks_stores_unknown_targets_by_canonicalized_url(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    target_url = "https://external.site/not-ingested"
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/source",
        title="Source",
        published_at=None,
        content_markdown=f"[unknown]({target_url})",
    )

    service.embed_document_chunks(document.id)

    link_row = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ?",
        (document.id,),
    ).fetchone()

    assert link_row is not None
    assert link_row["to_document_id"] == service_module.document_id_for_url(
        service_module._canonicalize_url(target_url)
    )


def test_outbound_links_ignore_self_and_follow_content_delete_and_refresh_lifecycle(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    canonical_url = "https://example.com/lifecycle"
    document = service.upsert_document(
        source_id=source.id,
        canonical_url=canonical_url,
        title="Lifecycle",
        published_at=None,
        content_markdown=f"[self]({canonical_url}) [other](https://other.example/other)",
    )

    service.embed_document_chunks(document.id)

    links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ? ORDER BY to_document_id",
        (document.id,),
    ).fetchall()
    assert [row["to_document_id"] for row in links] == [
        service_module.document_id_for_url(service_module._canonicalize_url("https://other.example/other"))
    ]

    updated = service.upsert_document(
        source_id=source.id,
        canonical_url=canonical_url,
        title="Lifecycle updated",
        published_at=None,
        content_markdown="updated body with no links",
    )

    stale_links = service.connection.execute(
        "SELECT COUNT(*) AS count FROM links WHERE from_document_id = ?",
        (updated.id,),
    ).fetchone()
    assert stale_links["count"] == 0

    refreshed = service.upsert_document(
        source_id=source.id,
        canonical_url=canonical_url,
        title="Lifecycle refreshed",
        published_at=None,
        content_markdown="[refreshed](https://external.example/refreshed)",
    )

    refreshed_links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ?",
        (refreshed.id,),
    ).fetchall()
    assert [row["to_document_id"] for row in refreshed_links] == [
        service_module.document_id_for_url(service_module._canonicalize_url("https://external.example/refreshed"))
    ]

    assert service.delete_document(updated.id) is True
    remaining_links = service.connection.execute(
        "SELECT COUNT(*) AS count FROM links WHERE from_document_id = ?",
        (updated.id,),
    ).fetchone()
    assert remaining_links["count"] == 0


# Search behavior

def test_rank_fusion_search_returns_results(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello",
        published_at=None,
        content_markdown="Hello world from the search system.",
    )
    service.embed_document_chunks(document.id)

    results = service.search("hello", limit=5)

    assert results
    assert results[0].document.canonical_url == "https://example.com/hello"
    assert "hello" in results[0].chunk.content_text.lower()


def test_rank_fusion_scores_are_reciprocal_and_additive(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    for idx in range(3):
        service.upsert_document(
            source_id=source.id,
            canonical_url=f"https://example.com/{idx}",
            title=f"Doc {idx}",
            published_at=None,
            content_markdown="alpha alpha",
        )
    service.synchronize_document_embeddings()

    results = service.search("alpha", limit=3)

    assert len(results) == 3
    chunk_ids = [result.chunk.id for result in results]
    assert chunk_ids == sorted(chunk_ids)

    for rank, result in enumerate(results, start=1):
        expected_method_score = pytest.approx(1.0 / (1 + rank))
        assert result.fts_score == expected_method_score
        assert result.vector_score == expected_method_score
        assert result.link_score == 0.0
        assert result.score == pytest.approx(result.fts_score + result.vector_score + result.link_score)


def test_rank_fusion_zero_fills_missing_method_score(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/vector-only",
        title="Vector Only",
        published_at=None,
        content_markdown="alpha alpha",
    )
    service.synchronize_document_embeddings()

    results = service.search("nonexistentterm", limit=5)

    assert results
    top = results[0]
    assert top.fts_score == 0.0
    assert top.vector_score > 0.0
    assert top.link_score == 0.0
    assert top.score == pytest.approx(top.fts_score + top.vector_score + top.link_score)


def test_search_respects_result_limit(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    for index in range(5):
        service.upsert_document(
            source_id=source.id,
            canonical_url=f"https://example.com/doc-{index}",
            title=f"Doc {index}",
            published_at=None,
            content_markdown="alpha",
        )
    service.synchronize_document_embeddings()

    results = service.search("alpha", limit=2)

    assert len(results) == 2


def test_search_returns_empty_for_blank_query_or_non_positive_limit(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/searchable",
        title="Searchable",
        published_at=None,
        content_markdown="hello world",
    )
    service.embed_document_chunks(document.id)

    assert service.search("   ", limit=5) == []
    assert service.search("hello", limit=0) == []
    assert service.search("hello", limit=-1) == []


def test_search_includes_link_score_with_deterministic_ties_and_zero_fill(service: SearchService):
    source_a = service.upsert_source("alpha.example", name="Alpha")
    source_b = service.upsert_source("beta.example", name="Beta")
    source_c = service.upsert_source("gamma.example", name="Gamma")
    source_d = service.upsert_source("delta.example", name="Delta")

    doc_a = service.upsert_document(
        source_id=source_a.id,
        canonical_url="https://alpha.example/a",
        title="A",
        published_at=None,
        content_markdown="alpha",
    )
    doc_b = service.upsert_document(
        source_id=source_b.id,
        canonical_url="https://beta.example/b",
        title="B",
        published_at=None,
        content_markdown=f"alpha [a]({doc_a.canonical_url})",
    )
    doc_c = service.upsert_document(
        source_id=source_c.id,
        canonical_url="https://gamma.example/c",
        title="C",
        published_at=None,
        content_markdown=f"alpha [a]({doc_a.canonical_url})",
    )
    doc_d = service.upsert_document(
        source_id=source_d.id,
        canonical_url="https://delta.example/d",
        title="D",
        published_at=None,
        content_markdown=f"alpha [b]({doc_b.canonical_url}) [c]({doc_c.canonical_url})",
    )

    service.embed_document_chunks(doc_a.id)
    service.embed_document_chunks(doc_b.id)
    service.embed_document_chunks(doc_c.id)
    service.embed_document_chunks(doc_d.id)

    results = service.search("alpha", limit=4)

    assert len(results) == 4

    by_document_id = {result.document.id: result for result in results}
    for result in results:
        assert result.score == pytest.approx(result.fts_score + result.vector_score + result.link_score)

    assert by_document_id[doc_a.id].link_score == pytest.approx(1.0 / (1 + 1))
    assert by_document_id[doc_d.id].link_score == 0.0

    tied_doc_ids = sorted([doc_b.id, doc_c.id])
    assert by_document_id[tied_doc_ids[0]].link_score == pytest.approx(1.0 / (1 + 2))
    assert by_document_id[tied_doc_ids[1]].link_score == pytest.approx(1.0 / (1 + 3))


def test_search_result_model_dump_contains_link_score(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/result-shape",
        title="Result shape",
        published_at=None,
        content_markdown="alpha",
    )
    service.embed_document_chunks(document.id)

    results = service.search("alpha", limit=1)

    assert len(results) == 1
    payload = results[0].model_dump()
    assert "link_score" in payload
    assert isinstance(payload["link_score"], float)


# Ingestion behavior implemented in service.py

def test_non_feed_http_get_uses_configured_browser_headers(service: SearchService):
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, text="ok")

    service._http_client.close()
    service._http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=service_module._DEFAULT_HEADERS,
    )

    service._http_get("https://example.com/header-check")

    request = captured["request"]
    for header_name, expected_value in service_module._DEFAULT_HEADERS.items():
        assert request.headers.get(header_name) == expected_value


def test_non_feed_http_get_maintains_cookies_for_service_run(service: SearchService):
    seen_cookie_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_cookie_headers.append(request.headers.get("cookie"))
        if request.url.path == "/set-cookie":
            return httpx.Response(200, headers={"Set-Cookie": "sessionid=abc123; Path=/"}, text="set")
        return httpx.Response(200, text="ok")

    service._http_client.close()
    service._http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers=service_module._DEFAULT_HEADERS,
    )

    service._http_get("https://example.com/set-cookie")
    service._http_get("https://example.com/follow-up")

    assert seen_cookie_headers == [None, "sessionid=abc123"]


def test_create_document_from_url(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    assert document.canonical_url == f"{http_server}/canonical"
    assert len(document.content_hash) == 6
    assert all(char in "0123456789abcdef" for char in document.content_hash)

    chunk_rows = service.connection.execute(
        "SELECT COUNT(*) AS count FROM chunks WHERE document_id = ?",
        (document.id,),
    ).fetchone()
    assert chunk_rows["count"] > 0

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.canonical_domain == urlparse(document.canonical_url).netloc


def test_create_document_from_url_falls_back_to_requested_url_when_canonical_missing(
    service: SearchService,
    http_server,
):
    document = service.create_document_from_url(f"{http_server}/article-no-canonical")

    assert document.canonical_url == f"{http_server}/article-no-canonical"


def test_create_document_from_url_extracts_published_time_metadata(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article-published")

    assert document.published_at == datetime(2025, 1, 9, 14, 30, tzinfo=timezone.utc)


def test_create_document_from_url_cleans_noisy_content_and_preserves_cleaned_links(
    service: SearchService,
    http_server,
):
    document = service.create_document_from_url(f"{http_server}/article-noisy")

    chunk_text = " ".join(_chunk_texts(service, document.id))
    assert "console.log" not in chunk_text
    assert "BUY BUY BUY" not in chunk_text
    assert "Odd spacing and text cleanup." in chunk_text
    assert "Readable prose with a kept link" in chunk_text

    links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ? ORDER BY to_document_id",
        (document.id,),
    ).fetchall()

    assert [row["to_document_id"] for row in links] == sorted(
        [
            service_module.document_id_for_url("https://external.example/kept"),
            service_module.document_id_for_url("https://external.example/preserved-from-dropped"),
            service_module.document_id_for_url("http://external.example/from-relative"),
        ]
    )


def test_create_document_from_url_rejects_empty_after_cleanup(service: SearchService, http_server):
    with pytest.raises(ValueError, match="Empty content"):
        service.create_document_from_url(f"{http_server}/article-low-signal-only")


def test_create_documents_from_feed_uses_shared_cleanup_pipeline(service: SearchService, monkeypatch):
    class Entry(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:  # pragma: no cover - parity with dict attribute lookup
                raise AttributeError(item) from exc

    parsed = SimpleNamespace(
        feed={"title": "Shared Cleanup Feed"},
        entries=[
            Entry(
                title="Cleaned Feed Entry",
                link="https://feed.example/entry",
                content=[
                    SimpleNamespace(
                        value=(
                            "<p>Hello\u200b world.</p>"
                            "<p>" + " ".join(["BUY"] * 70) + " "
                            '<a href="https://external.example/feed-dropped">drop-link</a></p>'
                            '<script>console.log("noise")</script>'
                        )
                    )
                ],
            )
        ],
        status=200,
        bozo=0,
    )

    monkeypatch.setattr("feedparser.parse", lambda _url: parsed)

    documents = service.create_documents_from_feed("https://feed.example/rss")

    assert len(documents) == 1
    chunk_text = " ".join(_chunk_texts(service, documents[0].id))
    assert "Hello world." in chunk_text
    assert "console.log" not in chunk_text
    assert "BUY BUY BUY" not in chunk_text

    links = service.connection.execute(
        "SELECT to_document_id FROM links WHERE from_document_id = ?",
        (documents[0].id,),
    ).fetchall()
    assert [row["to_document_id"] for row in links] == [
        service_module.document_id_for_url("https://external.example/feed-dropped")
    ]


@pytest.mark.parametrize(
    "path",
    [
        "backoff-403",
        "backoff-429",
        "backoff-503",
        "backoff-retry-after",
        "backoff-captcha",
    ],
)
def test_create_document_from_url_raises_on_backoff_signals(service: SearchService, http_server, path: str):
    with pytest.raises(BackoffError):
        service.create_document_from_url(f"{http_server}/{path}")


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("backoff-403", "status_code=403"),
        ("backoff-429", "status_code=429"),
        ("backoff-503", "status_code=503"),
        ("backoff-retry-after", "retry-after-header"),
        ("backoff-captcha", "body-marker=recaptcha"),
    ],
)
def test_create_document_from_url_backoff_error_includes_reason(
    service: SearchService,
    http_server,
    path: str,
    reason: str,
):
    with pytest.raises(BackoffError, match=reason):
        service.create_document_from_url(f"{http_server}/{path}")


def test_create_documents_from_feed(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed")

    assert len(documents) == 1
    document = documents[0]
    assert document.canonical_url == f"{http_server}/feed-entry"
    assert document.title == "Feed Entry"

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.rss_feed == f"{http_server}/feed"


def test_create_documents_from_feed_uses_summary_when_content_missing(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed-summary-and-empty")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/summary-entry"
    chunk_text = " ".join(_chunk_texts(service, documents[0].id))
    assert "Summary based content" in chunk_text


def test_create_documents_from_feed_backfills_missing_source_attributes(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    source_before = service.get_source(document.source_id)
    assert source_before is not None
    assert source_before.name is None
    assert source_before.rss_feed is None

    service.create_documents_from_feed(f"{http_server}/feed")

    source_after = service.get_source(document.source_id)
    assert source_after is not None
    assert source_after.name == "Test Feed"
    assert source_after.rss_feed == f"{http_server}/feed"


def test_create_documents_from_feed_pagination_disabled(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed-paginated")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/feed-paginated-entry-1"


def test_create_documents_from_feed_pagination_enabled(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed-paginated", paginate=True)

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/feed-paginated-entry-1" in urls
    assert f"{http_server}/feed-paginated-entry-2" in urls


def test_create_documents_from_feed_pagination_applies_minimum_one_second_interval(
    service: SearchService,
    http_server,
    monkeypatch,
):
    monotonic_values = iter([0.0, 0.2, 1.0, 1.8])
    sleep_calls: list[float] = []

    monkeypatch.setattr(service_module.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(service_module.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    documents = service.create_documents_from_feed(f"{http_server}/feed-paginated", paginate=True)

    assert len(documents) == 2
    assert sleep_calls == pytest.approx([0.8, 0.2])


def test_create_documents_from_feed_wordpress_pagination(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/wp-feed", paginate=True)

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/wp-feed-entry-1" in urls
    assert f"{http_server}/wp-feed-entry-2" in urls


def test_create_documents_from_feed_pagination_stops_on_loop(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed-loop", paginate=True)

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/feed-loop-entry"


def test_create_documents_from_feed_pagination_best_effort(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed-paginated-error", paginate=True)

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/feed-paginated-error-entry"


def test_create_documents_from_opml_multi_feed(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml")

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/feed-entry" in urls
    assert f"{http_server}/feed2-entry" in urls


def test_create_documents_from_opml_nested_outlines(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml-nested")

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/feed-entry" in urls
    assert f"{http_server}/feed2-entry" in urls


def test_create_documents_from_opml_deduplicates_feeds(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml-duplicates")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/feed-entry"


def test_create_documents_from_opml_invalid_xml_raises_value_error(service: SearchService, http_server):
    with pytest.raises(ValueError, match="Invalid OPML XML"):
        service.create_documents_from_opml(f"{http_server}/invalid-opml")


def test_create_documents_from_sitemap_ingests_all_url_entries(service: SearchService, http_server):
    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap.xml")

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/canonical" in urls
    assert f"{http_server}/canonical-2" in urls


def test_create_documents_from_sitemap_deduplicates_urls(service: SearchService, http_server):
    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap-duplicates.xml")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/canonical"


def test_create_documents_from_sitemap_skips_shop_paths(service: SearchService, http_server):
    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap-shop-skip.xml")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/canonical"


def test_create_documents_from_sitemap_invalid_xml_raises_value_error(service: SearchService, http_server):
    with pytest.raises(ValueError, match="Invalid sitemap XML"):
        service.create_documents_from_sitemap(f"{http_server}/invalid-sitemap.xml")


def test_create_documents_from_sitemap_bootstrap_skips_existing_urls(service: SearchService, http_server):
    source = service.upsert_source(urlparse(http_server).netloc)
    service.upsert_document(
        source_id=source.id,
        canonical_url=f"{http_server}/backoff-403",
        title="Already ingested",
        published_at=None,
        content_markdown="existing",
    )

    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap-bootstrap-skip.xml", bootstrap=True)

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/canonical-2"


@pytest.mark.parametrize(
    "sitemap_path",
    [
        "sitemap-backoff-429.xml",
        "sitemap-backoff-503.xml",
        "sitemap-backoff-retry-after.xml",
        "sitemap-backoff-captcha.xml",
    ],
)
def test_create_documents_from_sitemap_raises_on_backoff_signals(
    service: SearchService,
    http_server,
    sitemap_path: str,
):
    with pytest.raises(BackoffError):
        service.create_documents_from_sitemap(f"{http_server}/{sitemap_path}")


def test_create_documents_from_sitemap_halts_on_backoff_and_keeps_prior_documents(service: SearchService, http_server):
    with pytest.raises(BackoffError):
        service.create_documents_from_sitemap(f"{http_server}/sitemap-backoff-403.xml")

    stored_documents = service.list_documents()
    assert len(stored_documents) == 1
    assert stored_documents[0].canonical_url == f"{http_server}/canonical"


def test_search_service_supports_context_manager(tmp_path):
    db_path = tmp_path / "ctx" / "search.db"

    with SearchService(db_path) as managed:
        managed.connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        managed.connection.execute("SELECT 1")


def test_get_source_missing_and_list_sources_order(service: SearchService):
    assert service.get_source("missing") is None

    source_b = service.upsert_source("b.example", name="B")
    source_a = service.upsert_source("a.example", name="A")

    sources = service.list_sources()

    assert [source.id for source in sources] == [source_a.id, source_b.id]


def test_document_has_chunks_reflects_chunk_lifecycle(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/chunks",
        title="Chunks",
        published_at=None,
        content_markdown="chunk me",
    )

    assert service.document_has_chunks(document.id) is True

    assert service.delete_document(document.id) is True
    assert service.document_has_chunks(document.id) is False


def test_parse_datetime_returns_none_for_invalid_values():
    assert service_module._parse_datetime(None) is None
    assert service_module._parse_datetime("not a date") is None


def test_classify_backoff_response_checks_captcha_markers_only_in_html_body():
    head_only = httpx.Response(
        200,
        text="<html><head><title>captcha challenge</title></head><body>all clear</body></html>",
    )
    assert service_module._classify_backoff_response(head_only) is None

    body_marker = httpx.Response(
        200,
        text="<html><head><title>ok</title></head><body>Please verify you are human</body></html>",
    )
    assert service_module._classify_backoff_response(body_marker) == "body-marker=verify you are human"


def test_search_returns_empty_when_ranked_chunk_rows_are_missing(service: SearchService):
    service.connection.execute(
        "INSERT INTO chunks_vec (rowid, embedding) VALUES (?, ?)",
        (9999, service._sqlite_vec.serialize_float32([0.0] * 768)),
    )
    service.connection.commit()

    assert service.search("orphan chunk", limit=5) == []


def test_search_skips_chunk_ids_missing_after_scoring(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    doc_a = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/missing-after-score-a",
        title="A",
        published_at=None,
        content_markdown="alpha",
    )
    doc_b = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/missing-after-score-b",
        title="B",
        published_at=None,
        content_markdown="alpha",
    )
    service.synchronize_document_embeddings()

    real_connection = service.connection

    class DeletingConnectionProxy:
        def __init__(self, connection):
            self._connection = connection
            self._deleted = False

        def execute(self, sql, params=()):
            if (
                "FROM chunks" in sql
                and "JOIN documents ON documents.id = chunks.document_id" in sql
                and "WHERE chunks.id IN" in sql
                and not self._deleted
                and params
            ):
                self._connection.execute("DELETE FROM chunks WHERE id = ?", (params[0],))
                self._connection.commit()
                self._deleted = True
            return self._connection.execute(sql, params)

        def __getattr__(self, name):
            return getattr(self._connection, name)

    service.connection = DeletingConnectionProxy(real_connection)
    try:
        results = service.search("alpha", limit=2)
    finally:
        service.connection = real_connection

    assert len(results) == 1
    assert results[0].document.id in {doc_a.id, doc_b.id}


def test_create_document_from_url_rejects_empty_extracted_content(service: SearchService, http_server, monkeypatch):
    class EmptyReadable:
        def __init__(self, _html: str):
            pass

        def summary(self):
            return ""

        def short_title(self):
            return ""

    monkeypatch.setattr(service_module, "ReadabilityDocument", EmptyReadable)

    with pytest.raises(ValueError, match="Empty content"):
        service.create_document_from_url(f"{http_server}/article")


def test_create_documents_from_feed_skips_entries_without_url_or_content(service: SearchService, monkeypatch):
    class Entry(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:  # pragma: no cover - parity with dict attribute lookup
                raise AttributeError(item) from exc

    parsed = SimpleNamespace(
        feed={"title": "Edge Feed"},
        entries=[
            Entry(title="No URL", summary="<p>summary exists</p>"),
            Entry(title="No Content", link="https://example.com/no-content"),
        ],
        status=200,
        bozo=0,
    )

    monkeypatch.setattr("feedparser.parse", lambda _url: parsed)

    documents = service.create_documents_from_feed("https://example.com/feed")

    assert documents == []


def test_create_documents_from_feed_wordpress_dict_generator_and_invalid_paged_value(
    service: SearchService,
    monkeypatch,
):
    urls_seen: list[str] = []

    def fake_parse(url: str):
        urls_seen.append(url)
        if "paged=2" in url:
            return SimpleNamespace(feed={"title": "WP", "generator": "WordPress"}, entries=[], status=404, bozo=0)
        return SimpleNamespace(
            feed={"title": "WP", "generator": {"name": "WordPress"}},
            entries=[],
            status=200,
            bozo=0,
        )

    monkeypatch.setattr("feedparser.parse", fake_parse)

    documents = service.create_documents_from_feed("https://example.com/wp-feed?paged=oops", paginate=True)

    assert documents == []
    assert urls_seen == [
        "https://example.com/wp-feed?paged=oops",
        "https://example.com/wp-feed?paged=2",
    ]


def test_create_documents_from_feed_reraises_parse_error_on_first_page(service: SearchService, monkeypatch):
    def fake_parse(_url: str):
        raise RuntimeError("boom")

    monkeypatch.setattr("feedparser.parse", fake_parse)

    with pytest.raises(RuntimeError, match="boom"):
        service.create_documents_from_feed("https://example.com/feed", paginate=True)


def test_create_documents_from_feed_stops_after_parse_error_on_later_page(service: SearchService, monkeypatch):
    class Entry(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:  # pragma: no cover - parity with dict attribute lookup
                raise AttributeError(item) from exc

    calls = {"count": 0}

    def fake_parse(url: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return SimpleNamespace(
                feed={"title": "Paginated", "links": [{"rel": "next", "href": "https://example.com/feed-2"}]},
                entries=[
                    Entry(
                        title="Entry 1",
                        link="https://example.com/entry-1",
                        content=[SimpleNamespace(value="<p>hello</p>")],
                    )
                ],
                status=200,
                bozo=0,
            )
        raise RuntimeError(f"failed for {url}")

    monkeypatch.setattr("feedparser.parse", fake_parse)

    documents = service.create_documents_from_feed("https://example.com/feed", paginate=True)

    assert len(documents) == 1
    assert documents[0].canonical_url == "https://example.com/entry-1"


def test_create_documents_from_opml_continues_when_one_feed_ingestion_fails(
    service: SearchService,
    http_server,
    monkeypatch,
):
    fallback_document = Document(
        id="doc-fallback",
        source_id="source-fallback",
        canonical_url="https://example.com/fallback",
        title="Fallback",
        published_at=None,
        content_hash="d0f631",
    )

    def fake_create_documents_from_feed(feed_url: str, paginate: bool = False):  # noqa: ARG001 - signature parity
        if feed_url.endswith("/feed"):
            raise RuntimeError("feed failed")
        return [fallback_document]

    monkeypatch.setattr(service, "create_documents_from_feed", fake_create_documents_from_feed)

    documents = service.create_documents_from_opml(f"{http_server}/opml")

    assert documents == [fallback_document]


def test_create_documents_from_feed_ignores_non_next_links_when_paging(service: SearchService, monkeypatch):
    class Entry(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:  # pragma: no cover - parity with dict attribute lookup
                raise AttributeError(item) from exc

    seen_urls: list[str] = []

    def fake_parse(url: str):
        seen_urls.append(url)
        if url.endswith("page-2"):
            return SimpleNamespace(feed={"title": "Feed"}, entries=[], status=200, bozo=0)
        return SimpleNamespace(
            feed={
                "title": "Feed",
                "links": [
                    {"rel": "self", "href": "https://example.com/feed"},
                    {"rel": "next", "href": "https://example.com/page-2"},
                ],
            },
            entries=[
                Entry(
                    title="Entry 1",
                    link="https://example.com/entry-1",
                    content=[SimpleNamespace(value="<p>hello</p>")],
                )
            ],
            status=200,
            bozo=0,
        )

    monkeypatch.setattr("feedparser.parse", fake_parse)

    documents = service.create_documents_from_feed("https://example.com/feed", paginate=True)

    assert len(documents) == 1
    assert seen_urls == ["https://example.com/feed", "https://example.com/page-2"]


def test_create_documents_from_feed_stops_on_bozo_second_page_with_no_entries(service: SearchService, monkeypatch):
    class Entry(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:  # pragma: no cover - parity with dict attribute lookup
                raise AttributeError(item) from exc

    parse_count = {"count": 0}

    def fake_parse(url: str):
        parse_count["count"] += 1
        if parse_count["count"] == 1:
            return SimpleNamespace(
                feed={"title": "Feed", "links": [{"rel": "next", "href": "https://example.com/bozo-2"}]},
                entries=[
                    Entry(
                        title="Entry 1",
                        link="https://example.com/entry-1",
                        content=[SimpleNamespace(value="<p>hello</p>")],
                    )
                ],
                status=200,
                bozo=0,
            )
        return SimpleNamespace(feed={"title": "Feed"}, entries=[], status=200, bozo=1)

    monkeypatch.setattr("feedparser.parse", fake_parse)

    documents = service.create_documents_from_feed("https://example.com/feed", paginate=True)

    assert len(documents) == 1
    assert documents[0].canonical_url == "https://example.com/entry-1"


def test_create_documents_from_feed_pagination_caps_at_100_pages(service: SearchService, monkeypatch):
    visited: list[str] = []

    def fake_parse(url: str):
        visited.append(url)
        page = int(url.rsplit("=", 1)[-1])
        return SimpleNamespace(
            feed={"title": "Loop", "links": [{"rel": "next", "href": f"https://example.com/loop?page={page + 1}"}]},
            entries=[],
            status=200,
            bozo=0,
        )

    monkeypatch.setattr("feedparser.parse", fake_parse)

    documents = service.create_documents_from_feed("https://example.com/loop?page=1", paginate=True)

    assert documents == []
    assert len(visited) == 100


def test_search_returns_empty_when_no_chunks_match_query(service: SearchService):
    assert service.search("missing", limit=5) == []
