from __future__ import annotations

from urllib.parse import urlparse

from grogbot_search.service import SearchService


def test_create_document_from_url(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    assert document.canonical_url == f"{http_server}/canonical"
    assert "Article Heading" in document.content_markdown or "Hello world" in document.content_markdown

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.canonical_domain == urlparse(document.canonical_url).netloc


def test_create_documents_from_feed(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed")

    assert len(documents) == 1
    document = documents[0]
    assert document.canonical_url == f"{http_server}/feed-entry"
    assert document.title == "Feed Entry"

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.rss_feed == f"{http_server}/feed"
