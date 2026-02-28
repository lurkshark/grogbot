from __future__ import annotations

from urllib.parse import urlparse

import pytest

from grogbot_search.service import BackoffError, SearchService


def test_create_document_from_url(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    assert document.canonical_url == f"{http_server}/canonical"
    assert "Article Heading" in document.content_markdown or "Hello world" in document.content_markdown

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.canonical_domain == urlparse(document.canonical_url).netloc


@pytest.mark.parametrize(
    "path",
    [
        "backoff-403",
        "backoff-429",
        "backoff-503",
        "backoff-retry-after",
        "backoff-captcha",
    ],
)
def test_create_document_from_url_raises_on_backoff_signals(service: SearchService, http_server, path: str):
    with pytest.raises(BackoffError):
        service.create_document_from_url(f"{http_server}/{path}")


def test_create_documents_from_feed(service: SearchService, http_server):
    documents = service.create_documents_from_feed(f"{http_server}/feed")

    assert len(documents) == 1
    document = documents[0]
    assert document.canonical_url == f"{http_server}/feed-entry"
    assert document.title == "Feed Entry"

    source = service.get_source(document.source_id)
    assert source is not None
    assert source.rss_feed == f"{http_server}/feed"


def test_create_documents_from_feed_backfills_missing_source_attributes(service: SearchService, http_server):
    document = service.create_document_from_url(f"{http_server}/article")

    source_before = service.get_source(document.source_id)
    assert source_before is not None
    assert source_before.name is None
    assert source_before.rss_feed is None

    service.create_documents_from_feed(f"{http_server}/feed")

    source_after = service.get_source(document.source_id)
    assert source_after is not None
    assert source_after.name == "Test Feed"
    assert source_after.rss_feed == f"{http_server}/feed"


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


def test_create_documents_from_sitemap_ingests_all_url_entries(service: SearchService, http_server):
    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap.xml")

    # Should ingest valid URLs and skip failures best-effort
    assert len(documents) == 2
    urls = {doc.canonical_url for doc in documents}
    assert f"{http_server}/canonical" in urls
    assert f"{http_server}/canonical-2" in urls


def test_create_documents_from_sitemap_deduplicates_urls(service: SearchService, http_server):
    documents = service.create_documents_from_sitemap(f"{http_server}/sitemap-duplicates.xml")

    assert len(documents) == 1
    assert documents[0].canonical_url == f"{http_server}/canonical"


@pytest.mark.parametrize(
    "sitemap_path",
    [
        "sitemap-backoff-429.xml",
        "sitemap-backoff-503.xml",
        "sitemap-backoff-retry-after.xml",
        "sitemap-backoff-captcha.xml",
    ],
)
def test_create_documents_from_sitemap_raises_on_backoff_signals(
    service: SearchService,
    http_server,
    sitemap_path: str,
):
    with pytest.raises(BackoffError):
        service.create_documents_from_sitemap(f"{http_server}/{sitemap_path}")


def test_create_documents_from_sitemap_halts_on_backoff_and_keeps_prior_documents(service: SearchService, http_server):
    with pytest.raises(BackoffError):
        service.create_documents_from_sitemap(f"{http_server}/sitemap-backoff-403.xml")

    stored_documents = service.list_documents()
    assert len(stored_documents) == 1
    assert stored_documents[0].canonical_url == f"{http_server}/canonical"
