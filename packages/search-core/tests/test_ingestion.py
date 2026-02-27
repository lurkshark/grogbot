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


def test_create_documents_from_opml_multi_feed(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml")

    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/feed-entry" in urls
    assert f"{http_server}/feed2-entry" in urls


def test_create_documents_from_opml_nested_outlines(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml-nested")

    # Should find feeds from nested outlines (2 valid, 1 invalid skipped)
    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/feed-entry" in urls
    assert f"{http_server}/feed2-entry" in urls


def test_create_documents_from_opml_deduplicates_feeds(service: SearchService, http_server):
    documents = service.create_documents_from_opml(f"{http_server}/opml-duplicates")

    # Should deduplicate and only process one feed
    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/feed-entry"
