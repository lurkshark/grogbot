from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from grogbot_search.service import SearchService


@pytest.fixture
def api_client(service: SearchService):
    """Create a FastAPI test client with the service dependency overridden."""
    from fastapi.testclient import TestClient
    from grogbot_api.app import app, get_service

    def override_get_service():
        try:
            yield service
        finally:
            pass

    app.dependency_overrides[get_service] = override_get_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api_ingest_opml_endpoint_exists(api_client):
    """Test that API endpoint exists and accepts opml_url parameter"""
    # Mock the service method directly to verify the route delegates correctly
    with patch.object(SearchService, "create_documents_from_opml", return_value=[]) as mock_opml:
        response = api_client.post("/search/ingest/opml", json={"opml_url": "http://example.com/opml"})

    assert response.status_code == 200
    mock_opml.assert_called_once_with("http://example.com/opml")


def test_api_ingest_opml_returns_documents(api_client, service: SearchService):
    """Test that API endpoint returns documents from create_documents_from_opml"""
    # Create some test documents
    source = service.upsert_source("example.com", name="Test")
    doc1 = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/doc1",
        title="Doc 1",
        published_at=None,
        content_markdown="Content 1",
    )
    doc2 = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/doc2",
        title="Doc 2",
        published_at=None,
        content_markdown="Content 2",
    )

    with patch.object(SearchService, "create_documents_from_opml", return_value=[doc1, doc2]):
        response = api_client.post("/search/ingest/opml", json={"opml_url": "http://example.com/opml"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Doc 1"
    assert data[1]["title"] == "Doc 2"


def test_cli_ingest_opml_command(service: SearchService, http_server):
    """Test that CLI command delegates to service.create_documents_from_opml"""
    from typer.testing import CliRunner
    from grogbot_cli.app import app as cli_app
    from grogbot_search import load_config

    runner = CliRunner()

    # Mock the config to use our test service's db_path
    config = load_config()
    config.db_path = service.db_path

    with patch("grogbot_cli.app.load_config", return_value=config):
        result = runner.invoke(cli_app, ["search", "ingest-opml", f"{http_server}/opml"])

    assert result.exit_code == 0
    # Output should be valid JSON array
    import json
    data = json.loads(result.output)
    assert len(data) == 2
    urls = {doc["canonical_url"] for doc in data}
    assert f"{http_server}/feed-entry" in urls
    assert f"{http_server}/feed2-entry" in urls


def test_cli_ingest_opml_output_matches_feed_ingest(service: SearchService, http_server):
    """Verify CLI OPML output shape matches feed ingestion output"""
    from typer.testing import CliRunner
    from grogbot_cli.app import app as cli_app
    from grogbot_search import load_config

    runner = CliRunner()

    config = load_config()
    config.db_path = service.db_path

    # First ingest a single feed to get reference output
    with patch("grogbot_cli.app.load_config", return_value=config):
        feed_result = runner.invoke(cli_app, ["search", "ingest-feed", f"{http_server}/feed"])

    assert feed_result.exit_code == 0
    import json
    feed_data = json.loads(feed_result.output)

    # Now ingest OPML and verify structure matches
    with patch("grogbot_cli.app.load_config", return_value=config):
        opml_result = runner.invoke(cli_app, ["search", "ingest-opml", f"{http_server}/opml"])

    assert opml_result.exit_code == 0
    opml_data = json.loads(opml_result.output)

    # Both should be arrays of documents with same fields
    assert isinstance(feed_data, list)
    assert isinstance(opml_data, list)
    if feed_data and opml_data:
        assert set(feed_data[0].keys()) == set(opml_data[0].keys())


def test_opml_request_model_validation(api_client):
    """Test that API validates the opml_url parameter is provided"""
    # Should return 422 if opml_url is missing or invalid
    response = api_client.post("/search/ingest/opml", json={})
    assert response.status_code == 422

    response = api_client.post("/search/ingest/opml", json={"opml_url": None})
    assert response.status_code == 422


def test_api_ingest_sitemap_endpoint_exists(api_client):
    """Test that API endpoint exists and accepts sitemap_url parameter"""
    with patch.object(SearchService, "create_documents_from_sitemap", return_value=[]) as mock_sitemap:
        response = api_client.post(
            "/search/ingest/sitemap",
            json={"sitemap_url": "http://example.com/sitemap.xml"},
        )

    assert response.status_code == 200
    mock_sitemap.assert_called_once_with("http://example.com/sitemap.xml")


def test_api_ingest_sitemap_returns_documents(api_client, service: SearchService):
    """Test that API endpoint returns documents from create_documents_from_sitemap"""
    source = service.upsert_source("example.com", name="Test")
    doc1 = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/doc1",
        title="Doc 1",
        published_at=None,
        content_markdown="Content 1",
    )
    doc2 = service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/doc2",
        title="Doc 2",
        published_at=None,
        content_markdown="Content 2",
    )

    with patch.object(SearchService, "create_documents_from_sitemap", return_value=[doc1, doc2]):
        response = api_client.post(
            "/search/ingest/sitemap",
            json={"sitemap_url": "http://example.com/sitemap.xml"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Doc 1"
    assert data[1]["title"] == "Doc 2"


def test_cli_ingest_sitemap_command(service: SearchService, http_server):
    """Test that CLI command delegates to service.create_documents_from_sitemap"""
    from typer.testing import CliRunner
    from grogbot_cli.app import app as cli_app
    from grogbot_search import load_config

    runner = CliRunner()

    config = load_config()
    config.db_path = service.db_path

    with patch("grogbot_cli.app.load_config", return_value=config):
        result = runner.invoke(cli_app, ["search", "ingest-sitemap", f"{http_server}/sitemap.xml"])

    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert len(data) == 2
    urls = {doc["canonical_url"] for doc in data}
    assert f"{http_server}/canonical" in urls
    assert f"{http_server}/canonical-2" in urls


def test_sitemap_request_model_validation(api_client):
    """Test that API validates the sitemap_url parameter is provided"""
    response = api_client.post("/search/ingest/sitemap", json={})
    assert response.status_code == 422

    response = api_client.post("/search/ingest/sitemap", json={"sitemap_url": None})
    assert response.status_code == 422


def test_cli_query_includes_full_content_by_default(service: SearchService):
    """Default query output should include chunk.content_text and document.content_markdown."""
    from typer.testing import CliRunner
    from grogbot_cli.app import app as cli_app
    from grogbot_search import load_config
    import json

    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/full",
        title="Full",
        published_at=None,
        content_markdown="hello world full content",
    )

    runner = CliRunner()
    config = load_config()
    config.db_path = service.db_path

    with patch("grogbot_cli.app.load_config", return_value=config):
        result = runner.invoke(cli_app, ["search", "query", "hello", "--limit", "1"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert "content_markdown" in data[0]["document"]
    assert "content_text" in data[0]["chunk"]


def test_cli_query_summary_omits_large_content_fields(service: SearchService):
    """Summary query output should omit chunk.content_text and document.content_markdown."""
    from typer.testing import CliRunner
    from grogbot_cli.app import app as cli_app
    from grogbot_search import load_config
    import json

    source = service.upsert_source("example.com", name="Example")
    service.upsert_document(
        source_id=source.id,
        canonical_url="https://example.com/summary",
        title="Summary",
        published_at=None,
        content_markdown="hello world summary content",
    )

    runner = CliRunner()
    config = load_config()
    config.db_path = service.db_path

    with patch("grogbot_cli.app.load_config", return_value=config):
        result = runner.invoke(cli_app, ["search", "query", "hello", "--limit", "1", "--summary"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert "content_markdown" not in data[0]["document"]
    assert "content_text" not in data[0]["chunk"]
