from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import typer
from dateutil import parser as date_parser

from grogbot_search import SearchService, load_config

app = typer.Typer(no_args_is_help=True)
search_app = typer.Typer(no_args_is_help=True)
app.add_typer(search_app, name="search")

source_app = typer.Typer(no_args_is_help=True)
document_app = typer.Typer(no_args_is_help=True)
search_app.add_typer(source_app, name="source")
search_app.add_typer(document_app, name="document")


def _service() -> SearchService:
    config = load_config()
    return SearchService(config.db_path)


def _dump(value) -> str:
    return json.dumps(value, indent=2, default=str)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return date_parser.parse(value)


@source_app.command("upsert")
def source_upsert(
    canonical_domain: str = typer.Argument(..., help="Canonical domain for the source"),
    name: Optional[str] = typer.Option(None, "--name"),
    rss_feed: Optional[str] = typer.Option(None, "--rss-feed"),
):
    with _service() as service:
        source = service.upsert_source(canonical_domain=canonical_domain, name=name, rss_feed=rss_feed)
    typer.echo(_dump(source.model_dump()))


@source_app.command("list")
def source_list():
    with _service() as service:
        sources = service.list_sources()
    typer.echo(_dump([source.model_dump() for source in sources]))


@source_app.command("get")
def source_get(source_id: str = typer.Argument(..., help="Source ID")):
    with _service() as service:
        source = service.get_source(source_id)
    if not source:
        raise typer.Exit(code=1)
    typer.echo(_dump(source.model_dump()))


@source_app.command("delete")
def source_delete(source_id: str = typer.Argument(..., help="Source ID")):
    with _service() as service:
        deleted = service.delete_source(source_id)
    typer.echo(_dump({"deleted": deleted}))


@document_app.command("upsert")
def document_upsert(
    source_id: str = typer.Option(..., "--source-id"),
    canonical_url: str = typer.Option(..., "--canonical-url"),
    content_markdown: str = typer.Option(..., "--content-markdown"),
    title: Optional[str] = typer.Option(None, "--title"),
    author: Optional[str] = typer.Option(None, "--author"),
    published_at: Optional[str] = typer.Option(None, "--published-at"),
):
    with _service() as service:
        document = service.upsert_document(
            source_id=source_id,
            canonical_url=canonical_url,
            title=title,
            author=author,
            published_at=_parse_datetime(published_at),
            content_markdown=content_markdown,
        )
    typer.echo(_dump(document.model_dump()))


@document_app.command("list")
def document_list(source_id: Optional[str] = typer.Option(None, "--source-id")):
    with _service() as service:
        documents = service.list_documents(source_id=source_id)
    typer.echo(_dump([doc.model_dump() for doc in documents]))


@document_app.command("get")
def document_get(document_id: str = typer.Argument(..., help="Document ID")):
    with _service() as service:
        document = service.get_document(document_id)
    if not document:
        raise typer.Exit(code=1)
    typer.echo(_dump(document.model_dump()))


@document_app.command("delete")
def document_delete(document_id: str = typer.Argument(..., help="Document ID")):
    with _service() as service:
        deleted = service.delete_document(document_id)
    typer.echo(_dump({"deleted": deleted}))


@search_app.command("ingest-url")
def ingest_url(url: str = typer.Argument(..., help="URL to ingest")):
    with _service() as service:
        document = service.create_document_from_url(url)
    typer.echo(_dump(document.model_dump()))


@search_app.command("ingest-feed")
def ingest_feed(feed_url: str = typer.Argument(..., help="Feed URL to ingest")):
    with _service() as service:
        documents = service.create_documents_from_feed(feed_url)
    typer.echo(_dump([doc.model_dump() for doc in documents]))


@search_app.command("query")
def query(text: str = typer.Argument(..., help="Search query"), limit: int = typer.Option(10, "--limit")):
    with _service() as service:
        results = service.search(text, limit=limit)
    typer.echo(_dump([result.model_dump() for result in results]))
