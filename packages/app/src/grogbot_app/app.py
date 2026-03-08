from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from grogbot_search import SearchService, load_config
from grogbot_search.models import SearchResult

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
SNIPPET_LENGTH = 120
SNIPPET_MATCH_LEAD = 24

app = FastAPI(title="Grogbot App")
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@dataclass(frozen=True)
class SearchResultView:
    result: SearchResult
    snippet_text: str
    snippet_html: Markup

    @property
    def document(self):
        return self.result.document

    @property
    def chunk(self):
        return self.result.chunk


def search_results(query: str, *, limit: int = 25):
    config = load_config()
    with SearchService(config.db_path) as service:
        return service.search(query, limit=limit)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _query_terms(query: str) -> list[str]:
    raw_terms = re.findall(r"\w+", query.lower())
    seen: set[str] = set()

    meaningful = [term for term in raw_terms if len(term) >= 3]
    if not meaningful:
        meaningful = [term for term in raw_terms if term]

    ordered_terms: list[str] = []
    for term in meaningful:
        if term in seen:
            continue
        seen.add(term)
        ordered_terms.append(term)
    return ordered_terms


def _first_match_start(text: str, terms: Iterable[str]) -> int | None:
    earliest: int | None = None
    for term in terms:
        match = re.search(re.escape(term), text, flags=re.IGNORECASE)
        if match is None:
            continue
        if earliest is None or match.start() < earliest:
            earliest = match.start()
    return earliest


def _align_to_word_start(text: str, index: int) -> int:
    if index <= 0:
        return 0

    while index < len(text) and not text[index].isalnum():
        index += 1

    while index > 0 and text[index - 1].isalnum():
        index -= 1

    return index


def _truncate_excerpt(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    candidate = text[:max_chars].rstrip()
    last_space = candidate.rfind(" ")
    if last_space >= max_chars // 2:
        candidate = candidate[:last_space].rstrip()

    return f"{candidate}…"


def build_display_snippet(text: str, query: str, *, max_chars: int = SNIPPET_LENGTH) -> str:
    normalized = _normalize_whitespace(text)
    if len(normalized) <= max_chars:
        return normalized

    terms = _query_terms(query)
    start = 0
    match_start = _first_match_start(normalized, terms)
    if match_start is not None:
        start = _align_to_word_start(normalized, max(0, match_start - SNIPPET_MATCH_LEAD))

    excerpt = normalized[start:]
    return _truncate_excerpt(excerpt, max_chars=max_chars)


def highlight_snippet(snippet: str, query: str) -> Markup:
    terms = _query_terms(query)
    if not terms:
        return escape(snippet)

    pattern = re.compile("|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)), re.IGNORECASE)
    parts: list[Markup] = []
    cursor = 0

    for match in pattern.finditer(snippet):
        start, end = match.span()
        if start > cursor:
            parts.append(escape(snippet[cursor:start]))
        parts.append(Markup("<mark>") + escape(snippet[start:end]) + Markup("</mark>"))
        cursor = end

    if cursor == 0:
        return escape(snippet)

    if cursor < len(snippet):
        parts.append(escape(snippet[cursor:]))

    return Markup("").join(parts)


def build_search_result_views(results: list[SearchResult], query: str) -> list[SearchResultView]:
    views: list[SearchResultView] = []
    for result in results:
        snippet_text = build_display_snippet(result.chunk.content_text, query)
        views.append(
            SearchResultView(
                result=result,
                snippet_text=snippet_text,
                snippet_html=highlight_snippet(snippet_text, query),
            )
        )
    return views


@app.get("/", response_class=HTMLResponse)
def root_page(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "page_title": "Grogbot",
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = ""):
    return templates.TemplateResponse(
        request,
        "search_landing.html",
        {
            "page_title": "Grogbot Search",
            "query": q.strip(),
        },
    )


@app.get("/search/query", response_class=HTMLResponse)
def search_query_page(request: Request, q: str | None = None):
    query = (q or "").strip()
    if not query:
        return RedirectResponse(url="/search", status_code=302)

    results = search_results(query, limit=25)
    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "page_title": f"{query} - Grogbot Search",
            "query": query,
            "results": build_search_result_views(results, query),
        },
    )
