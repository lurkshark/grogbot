from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib  # type: ignore

import typer
from dateutil import parser as date_parser

from grogbot_search import DocumentNotFoundError, SearchService, load_config

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


def _bootstrap_sources_path() -> Path:
    return Path(__file__).resolve().parents[4] / "sources.toml"


def _load_bootstrap_sources(path: Path) -> list[dict[str, Optional[str]]]:
    if not path.exists():
        raise ValueError(f"sources.toml not found at {path}")

    with path.open("rb") as handle:
        data = tomllib.load(handle)

    entries = data.get("source", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        raise ValueError("sources.toml must define [[source]] entries")

    sources: list[dict[str, Optional[str]]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"source entry #{index + 1} must be a table")
        sources.append({"sitemap": entry.get("sitemap"), "feed": entry.get("feed")})

    return sources


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
    published_at: Optional[str] = typer.Option(None, "--published-at"),
):
    with _service() as service:
        try:
            document = service.upsert_document(
                source_id=source_id,
                canonical_url=canonical_url,
                title=title,
                published_at=_parse_datetime(published_at),
                content_markdown=content_markdown,
            )
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
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


@document_app.command("chunk")
def document_chunk(document_id: str = typer.Argument(..., help="Document ID")):
    with _service() as service:
        try:
            count = service.chunk_document(document_id)
        except DocumentNotFoundError as exc:
            typer.echo("Document not found", err=True)
            raise typer.Exit(code=1) from exc
    typer.echo(_dump({"chunks_created": count}))


@document_app.command("chunk-sync")
def document_chunk_sync(maximum: Optional[int] = typer.Option(None, "--maximum")):
    with _service() as service:
        count = service.synchronize_document_chunks(maximum=maximum)
    typer.echo(_dump({"chunks_created": count}))


@search_app.command("ingest-url")
def ingest_url(
    url: str = typer.Argument(..., help="URL to ingest"),
    chunk: bool = typer.Option(False, "--chunk", is_flag=True, help="Immediately chunk ingested documents"),
):
    with _service() as service:
        try:
            document = service.create_document_from_url(url)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        if chunk and not service.document_has_chunks(document.id):
            service.chunk_document(document.id)
    typer.echo(_dump(document.model_dump()))


@search_app.command("ingest-feed")
def ingest_feed(
    feed_url: str = typer.Argument(..., help="Feed URL to ingest"),
    paginate: bool = typer.Option(False, "--paginate", help="Follow rel=next pagination"),
    chunk: bool = typer.Option(False, "--chunk", is_flag=True, help="Immediately chunk ingested documents"),
):
    with _service() as service:
        documents = service.create_documents_from_feed(feed_url, paginate=paginate)
        if chunk:
            for document in documents:
                if not service.document_has_chunks(document.id):
                    service.chunk_document(document.id)
    typer.echo(_dump([doc.model_dump() for doc in documents]))


@search_app.command("ingest-opml")
def ingest_opml(
    opml_url: str = typer.Argument(..., help="OPML URL to ingest"),
    paginate: bool = typer.Option(False, "--paginate", help="Follow rel=next pagination for feeds"),
    chunk: bool = typer.Option(False, "--chunk", is_flag=True, help="Immediately chunk ingested documents"),
):
    with _service() as service:
        documents = service.create_documents_from_opml(opml_url, paginate=paginate)
        if chunk:
            for document in documents:
                if not service.document_has_chunks(document.id):
                    service.chunk_document(document.id)
    typer.echo(_dump([doc.model_dump() for doc in documents]))


@search_app.command("ingest-sitemap")
def ingest_sitemap(
    sitemap_url: str = typer.Argument(..., help="Sitemap URL to ingest"),
    chunk: bool = typer.Option(False, "--chunk", is_flag=True, help="Immediately chunk ingested documents"),
):
    with _service() as service:
        documents = service.create_documents_from_sitemap(sitemap_url)
        if chunk:
            for document in documents:
                if not service.document_has_chunks(document.id):
                    service.chunk_document(document.id)
    typer.echo(_dump([doc.model_dump() for doc in documents]))


@search_app.command("bootstrap")
def bootstrap(
    skip_feeds: bool = typer.Option(False, "--skip-feeds", help="Skip bootstrapping feeds"),
    skip_sitemaps: bool = typer.Option(False, "--skip-sitemaps", help="Skip bootstrapping sitemaps"),
):
    sources_path = _bootstrap_sources_path()
    try:
        sources = _load_bootstrap_sources(sources_path)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    sources_list = list(sources)
    with _service() as service:
        if not skip_feeds:
            for source in sources_list:
                feed = source.get("feed")
                if not feed:
                    continue
                typer.echo(f"Scraping feed {feed}")
                try:
                    service.create_documents_from_feed(feed, paginate=True)
                except Exception as exc:
                    print(f"Bootstrap failed for feed {feed}: {exc}", file=sys.stderr)
        if not skip_sitemaps:
            for source in sources_list:
                sitemap = source.get("sitemap")
                if not sitemap:
                    continue
                typer.echo(f"Scraping sitemap {sitemap}")
                try:
                    service.create_documents_from_sitemap(sitemap, bootstrap=True)
                except Exception as exc:
                    print(f"Bootstrap failed for sitemap {sitemap}: {exc}", file=sys.stderr)


@search_app.command("query")
def query(
    text: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit"),
    summary: bool = typer.Option(
        False,
        "--summary",
        help="Omit content_markdown/content_text from each search result",
    ),
):
    with _service() as service:
        results = service.search(text, limit=limit)

    exclude = None
    if summary:
        exclude = {
            "document": {"content_markdown"},
            "chunk": {"content_text"},
        }

    typer.echo(_dump([result.model_dump(exclude=exclude) for result in results]))
