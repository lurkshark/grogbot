from __future__ import annotations

import importlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from markupsafe import Markup

from grogbot_search.models import Chunk, Document, SearchResult

app_module = importlib.import_module("grogbot_app.app")


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


def test_root_page_renders_html_with_shared_branding_chrome():
    with TestClient(app_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'class="app-topbar"' in response.text
    assert 'class="app-brand" href="/"' in response.text
    assert 'href="/search"' in response.text
    assert "/assets/app.css" in response.text


def test_search_page_renders_compact_form_with_shared_branding_chrome():
    with TestClient(app_module.app) as client:
        response = client.get("/search")

    assert response.status_code == 200
    assert 'class="app-topbar"' in response.text
    assert 'action="/search/query"' in response.text
    assert 'name="q"' in response.text
    assert 'placeholder="Search Grogbot"' in response.text
    assert ">Search<" in response.text


def test_search_query_redirects_without_query():
    with TestClient(app_module.app) as client:
        response = client.get("/search/query", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/search"


def test_search_query_redirects_blank_query():
    with TestClient(app_module.app) as client:
        response = client.get("/search/query?q=%20%20%20", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/search"


def test_build_display_snippet_prefers_query_match_and_trailing_ellipsis():
    text = (
        "Opening filler text that keeps going before we reach the important retrieval signal and then the keyword "
        "arrives with enough trailing context to force truncation at the end of the excerpt for compact display."
    )

    snippet = app_module.build_display_snippet(text, "keyword")

    assert len(snippet) <= 121
    assert "keyword" in snippet.lower()
    assert snippet.endswith("…")
    assert not snippet.startswith("Opening filler text")


def test_highlight_snippet_marks_only_visible_literal_matches():
    highlighted = app_module.highlight_snippet("Keyword rich text", "keyword")
    plain = app_module.highlight_snippet("Semantic result only", "keyword")

    assert highlighted == Markup("<mark>Keyword</mark> rich text")
    assert plain == Markup("Semantic result only")


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

    monkeypatch.setattr(app_module, "search_results", fake_search_results)

    with TestClient(app_module.app) as client:
        response = client.get("/search/query?q=hello+world")

    assert response.status_code == 200
    assert captured == [("hello world", 25)]
    assert 'class="app-topbar"' in response.text
    assert 'value="hello world"' in response.text
    assert response.text.count('class="search-result"') == 25
    assert response.text.count("https://example.com/shared") >= 2
    assert "Unique snippet 25" in response.text
    assert "Unique snippet 26" not in response.text
    assert response.text.index("Duplicate snippet 1") < response.text.index("Duplicate snippet 2")


def test_search_query_renders_compact_snippets_with_highlighting(monkeypatch):
    long_snippet = (
        "This introduction is intentionally long before the displayed excerpt starts later and shows Keyword with "
        "enough trailing context to demonstrate compact truncation in the HTML response while continuing with several "
        "additional details that should not remain visible in the final snippet."
    )
    fallback_snippet = (
        "A semantic result without literal overlap still needs a compact leading excerpt that trims down to a shorter "
        "result preview for mobile reading comfort."
    )

    def fake_search_results(query: str, *, limit: int = 25):
        return [
            _result(
                index=1,
                document_id="doc-1",
                canonical_url="https://example.com/keyword",
                title="Keyword Result",
                snippet=long_snippet,
            ),
            _result(
                index=2,
                document_id="doc-2",
                canonical_url="https://example.com/fallback",
                title="Fallback Result",
                snippet=fallback_snippet,
            ),
        ]

    monkeypatch.setattr(app_module, "search_results", fake_search_results)

    with TestClient(app_module.app) as client:
        response = client.get("/search/query?q=keyword")

    assert response.status_code == 200
    assert long_snippet not in response.text
    assert fallback_snippet not in response.text
    assert "compact truncation in the HTML response." not in response.text
    assert "result preview for mobile reading comfort." not in response.text
    assert "…" in response.text
    assert "<mark>Keyword</mark>" in response.text
    assert response.text.count("<mark>") == 1
