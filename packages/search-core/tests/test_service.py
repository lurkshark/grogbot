from __future__ import annotations

import pytest

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


def test_rank_fusion_search_returns_results(service: SearchService):
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

    results = service.search("alpha", limit=3)

    assert len(results) == 3
    chunk_ids = [result.chunk.id for result in results]
    assert chunk_ids == sorted(chunk_ids)

    for rank, result in enumerate(results, start=1):
        expected_method_score = pytest.approx(1.0 / (1 + rank))
        assert result.fts_score == expected_method_score
        assert result.vector_score == expected_method_score
        assert result.score == pytest.approx(result.fts_score + result.vector_score)


class _RecordingConnection:
    def __init__(self, connection):
        self._connection = connection
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params=()):
        self.calls.append((sql, params))
        return self._connection.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self._connection, name)


def test_search_uses_limit_times_ten_candidate_depth(service: SearchService):
    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/alpha",
        title="Alpha",
        published_at=None,
        content_markdown="alpha alpha",
    )

    recording_connection = _RecordingConnection(service.connection)
    service.connection = recording_connection

    service.search("alpha", limit=4)

    ranking_calls = [
        params
        for _, params in recording_connection.calls
        if isinstance(params, tuple) and len(params) == 5 and params[0] == "alpha"
    ]
    assert ranking_calls

    params = ranking_calls[-1]
    assert params[1] == 40
    assert params[3] == 40
    assert params[4] == 4
