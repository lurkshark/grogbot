from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import pytest

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
    service.chunk_document(document.id)
    initial_chunks = _chunk_texts(service, document.id)

    updated = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello again",
        published_at=None,
        content_markdown="Hello world updated content",
    )
    assert _chunk_texts(service, updated.id) == []
    service.chunk_document(updated.id)
    updated_chunks = _chunk_texts(service, updated.id)

    assert initial_chunks != updated_chunks


def test_upsert_document_without_content_change_preserves_existing_chunks(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/stable",
        title="Stable",
        published_at=None,
        content_markdown="stable body",
    )
    service.chunk_document(document.id)

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


def test_delete_document_cascades_chunks_and_vector_rows(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/deletable",
        title="Delete Me",
        published_at=None,
        content_markdown="alpha beta gamma",
    )
    service.chunk_document(document.id)

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


def test_chunk_document_returns_count(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    document = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/chunk",
        title="Chunk",
        published_at=None,
        content_markdown="Hello world",
    )

    created = service.chunk_document(document.id)

    row = service.connection.execute(
        "SELECT COUNT(*) AS count FROM chunks WHERE document_id = ?",
        (document.id,),
    ).fetchone()
    assert created == row["count"]
    assert created > 0


def test_chunk_document_missing_raises(service: SearchService):
    with pytest.raises(DocumentNotFoundError):
        service.chunk_document("missing-id")


def test_synchronize_document_chunks_respects_maximum(service: SearchService):
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

    created = service.synchronize_document_chunks(maximum=1)
    chunked_docs = service.connection.execute(
        "SELECT DISTINCT document_id FROM chunks ORDER BY document_id",
    ).fetchall()
    assert len(chunked_docs) == 1
    assert created == service.connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]

    service.synchronize_document_chunks()
    chunked_docs = service.connection.execute(
        "SELECT DISTINCT document_id FROM chunks ORDER BY document_id",
    ).fetchall()
    assert len(chunked_docs) == 2


def test_synchronize_document_chunks_non_positive_maximum_is_noop(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/noop",
        title="Noop",
        published_at=None,
        content_markdown="noop",
    )

    assert service.synchronize_document_chunks(maximum=0) == 0
    assert service.synchronize_document_chunks(maximum=-5) == 0
    chunk_count = service.connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
    assert chunk_count == 0


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
    service.chunk_document(document.id)

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
    service.synchronize_document_chunks()

    results = service.search("alpha", limit=3)

    assert len(results) == 3
    chunk_ids = [result.chunk.id for result in results]
    assert chunk_ids == sorted(chunk_ids)

    for rank, result in enumerate(results, start=1):
        expected_method_score = pytest.approx(1.0 / (1 + rank))
        assert result.fts_score == expected_method_score
        assert result.vector_score == expected_method_score
        assert result.score == pytest.approx(result.fts_score + result.vector_score)


def test_rank_fusion_zero_fills_missing_method_score(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/vector-only",
        title="Vector Only",
        published_at=None,
        content_markdown="alpha alpha",
    )
    service.synchronize_document_chunks()

    results = service.search("nonexistentterm", limit=5)

    assert results
    top = results[0]
    assert top.fts_score == 0.0
    assert top.vector_score > 0.0
    assert top.score == pytest.approx(top.fts_score + top.vector_score)


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
    service.synchronize_document_chunks()

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
    service.chunk_document(document.id)

    assert service.search("   ", limit=5) == []
    assert service.search("hello", limit=0) == []
    assert service.search("hello", limit=-1) == []


# Ingestion behavior implemented in service.py

def test_create_document_from_url(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    assert document.canonical_url == f"{http_server}/canonical"
    assert "Article Heading" in document.content_markdown or "Hello world" in document.content_markdown

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
        ("backoff-captcha", "body-marker=captcha"),
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
    assert "Summary based content" in documents[0].content_markdown


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
