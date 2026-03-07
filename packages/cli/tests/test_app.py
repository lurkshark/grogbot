from __future__ import annotations

import json

from typer.testing import CliRunner

import grogbot_cli.app as app_module
from grogbot_search import EmbeddingSyncProgress


class FakeService:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001 - context manager protocol
        return False

    def synchronize_document_embeddings(self, maximum=None, progress_callback=None):
        assert maximum == 2
        assert progress_callback is not None
        progress_callback(
            EmbeddingSyncProgress(total_documents=2, completed_documents=0, vectors_created=0)
        )
        progress_callback(
            EmbeddingSyncProgress(total_documents=2, completed_documents=1, vectors_created=3)
        )
        progress_callback(
            EmbeddingSyncProgress(total_documents=2, completed_documents=2, vectors_created=7)
        )
        return 7


def test_embed_sync_shows_progress_on_stderr_and_keeps_json_stdout(monkeypatch):
    runner = CliRunner()
    monotonic_values = iter([100.0, 100.0, 110.0, 120.0])

    monkeypatch.setattr(app_module, "_service", lambda: FakeService())
    monkeypatch.setattr(app_module.time, "monotonic", lambda: next(monotonic_values))

    result = runner.invoke(
        app_module.app,
        ["search", "document", "embed-sync", "--maximum", "2"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"vectors_created": 7}
    assert "documents" not in result.stdout

    assert "0/2 documents" in result.stderr
    assert "1/2 documents" in result.stderr
    assert "2/2 documents" in result.stderr
    assert "ETA" in result.stderr
