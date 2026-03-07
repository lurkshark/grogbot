from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from grogbot_search import SearchService, load_config

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"

app = FastAPI(title="Grogbot Web")
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def search_results(query: str, *, limit: int = 25):
    config = load_config()
    with SearchService(config.db_path) as service:
        return service.search(query, limit=limit)


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
            "results": results,
        },
    )
