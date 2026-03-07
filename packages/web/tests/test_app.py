from __future__ import annotations

import importlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from grogbot_search.models import Chunk, Document, SearchResult

web_app_module = importlib.import_module("grogbot_web.app")


def _result(*, index: int, document_id: str, canonical_url: str, title: str | None, snippet: str) -> SearchResult:
    document = Document(
        id=document_id,
        source_id="source-1",
        canonical_url=canonical_url,
        title=title,
        published_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        content_hash=f"hash{index:02d}",
    )
    chunk = Chunk(
        id=index,
        document_id=document_id,
        chunk_index=index - 1,
        content_text=snippet,
    )
    return SearchResult(
        chunk=chunk,
        document=document,
        score=1.0 / index,
        fts_score=1.0 / index,
        vector_score=0.0,
        link_score=0.0,
    )


def test_root_page_renders_html():
    with TestClient(web_app_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Grogbot" in response.text
    assert 'href="/search"' in response.text
    assert "/assets/app.css" in response.text


def test_search_page_renders_form():
    with TestClient(web_app_module.app) as client:
        response = client.get("/search")

    assert response.status_code == 200
    assert "Grogbot Search" in response.text
    assert 'action="/search/query"' in response.text
    assert 'name="q"' in response.text
    assert ">Search<" in response.text


def test_search_query_redirects_without_query():
    with TestClient(web_app_module.app) as client:
        response = client.get("/search/query", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/search"


def test_search_query_redirects_blank_query():
    with TestClient(web_app_module.app) as client:
        response = client.get("/search/query?q=%20%20%20", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/search"


def test_search_query_renders_top_25_results_and_preserves_duplicates(monkeypatch):
    captured: list[tuple[str, int]] = []
    results = [
        _result(
            index=1,
            document_id="doc-shared",
            canonical_url="https://example.com/shared",
            title="Shared Document",
            snippet="Duplicate snippet 1",
        ),
        _result(
            index=2,
            document_id="doc-shared",
            canonical_url="https://example.com/shared",
            title="Shared Document",
            snippet="Duplicate snippet 2",
        ),
    ]
    results.extend(
        _result(
            index=index,
            document_id=f"doc-{index}",
            canonical_url=f"https://example.com/article-{index}",
            title=f"Article {index}",
            snippet=f"Unique snippet {index}",
        )
        for index in range(3, 31)
    )

    def fake_search_results(query: str, *, limit: int = 25):
        captured.append((query, limit))
        return results[:limit]

    monkeypatch.setattr(web_app_module, "search_results", fake_search_results)

    with TestClient(web_app_module.app) as client:
        response = client.get("/search/query?q=hello+world")

    assert response.status_code == 200
    assert captured == [("hello world", 25)]
    assert 'value="hello world"' in response.text
    assert response.text.count('class="search-result"') == 25
    assert response.text.count("https://example.com/shared") >= 2
    assert "Unique snippet 25" in response.text
    assert "Unique snippet 26" not in response.text
    assert response.text.index("Duplicate snippet 1") < response.text.index("Duplicate snippet 2")
