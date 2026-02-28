from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from grogbot_search import SearchService, load_config

app = FastAPI()


class SourceUpsertRequest(BaseModel):
    canonical_domain: str
    name: Optional[str] = None
    rss_feed: Optional[str] = None


class DocumentUpsertRequest(BaseModel):
    source_id: str
    canonical_url: str
    content_markdown: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None


class IngestUrlRequest(BaseModel):
    url: str


class IngestFeedRequest(BaseModel):
    feed_url: str


class IngestOpmlRequest(BaseModel):
    opml_url: str


class IngestSitemapRequest(BaseModel):
    sitemap_url: str


def get_service():
    config = load_config()
    service = SearchService(config.db_path)
    try:
        yield service
    finally:
        service.close()


@app.get("/search/sources")
def list_sources(service: SearchService = Depends(get_service)):
    return service.list_sources()


@app.post("/search/sources")
def upsert_source(payload: SourceUpsertRequest, service: SearchService = Depends(get_service)):
    return service.upsert_source(
        canonical_domain=payload.canonical_domain,
        name=payload.name,
        rss_feed=payload.rss_feed,
    )


@app.get("/search/sources/{source_id}")
def get_source(source_id: str, service: SearchService = Depends(get_service)):
    source = service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@app.delete("/search/sources/{source_id}")
def delete_source(source_id: str, service: SearchService = Depends(get_service)):
    return {"deleted": service.delete_source(source_id)}


@app.get("/search/documents")
def list_documents(source_id: Optional[str] = None, service: SearchService = Depends(get_service)):
    return service.list_documents(source_id=source_id)


@app.post("/search/documents")
def upsert_document(payload: DocumentUpsertRequest, service: SearchService = Depends(get_service)):
    return service.upsert_document(
        source_id=payload.source_id,
        canonical_url=payload.canonical_url,
        title=payload.title,
        published_at=payload.published_at,
        content_markdown=payload.content_markdown,
    )


@app.get("/search/documents/{document_id}")
def get_document(document_id: str, service: SearchService = Depends(get_service)):
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/search/documents/{document_id}")
def delete_document(document_id: str, service: SearchService = Depends(get_service)):
    return {"deleted": service.delete_document(document_id)}


@app.post("/search/ingest/url")
def ingest_url(payload: IngestUrlRequest, service: SearchService = Depends(get_service)):
    return service.create_document_from_url(payload.url)


@app.post("/search/ingest/feed")
def ingest_feed(payload: IngestFeedRequest, service: SearchService = Depends(get_service)):
    return service.create_documents_from_feed(payload.feed_url)


@app.post("/search/ingest/opml")
def ingest_opml(payload: IngestOpmlRequest, service: SearchService = Depends(get_service)):
    return service.create_documents_from_opml(payload.opml_url)


@app.post("/search/ingest/sitemap")
def ingest_sitemap(payload: IngestSitemapRequest, service: SearchService = Depends(get_service)):
    return service.create_documents_from_sitemap(payload.sitemap_url)


@app.get("/search/query")
def query(q: str, limit: int = 10, service: SearchService = Depends(get_service)):
    return service.search(q, limit=limit)
