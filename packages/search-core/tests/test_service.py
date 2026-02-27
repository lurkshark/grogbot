from __future__ import annotations

from grogbot_search.service import SearchService


def _chunk_texts(service: SearchService, document_id: str) -> list[str]:
    rows = service.connection.execute(
        "SELECT content_text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document_id,),
    ).fetchall()
    return [row["content_text"] for row in rows]


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


def test_hybrid_search_returns_results(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/hello",
        title="Hello",
        published_at=None,
        content_markdown="Hello world from the search system.",
    )

    results = service.search("hello", limit=5)

    assert results
    assert results[0].document.canonical_url == "https://example.com/hello"
    assert "hello" in results[0].chunk.content_text.lower()
