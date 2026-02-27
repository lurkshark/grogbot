## 1. Search core OPML ingestion

- [ ] 1.1 Add OPML parsing helpers in `packages/search-core/src/grogbot_search/service.py` to fetch OPML XML and extract nested `outline` `xmlUrl` values.
- [ ] 1.2 Implement `SearchService.create_documents_from_opml(opml_url: str) -> List[Document]` that deduplicates feed URLs, calls `create_documents_from_feed`, and flattens results.
- [ ] 1.3 Implement best-effort behavior in OPML ingestion so feed-level failures are caught and do not stop processing remaining feeds.

## 2. API and CLI surface integration

- [ ] 2.1 Add `IngestOpmlRequest` and `POST /search/ingest/opml` in `packages/api/src/grogbot_api/app.py` delegating to `create_documents_from_opml`.
- [ ] 2.2 Add CLI command `search ingest-opml` in `packages/cli/src/grogbot_cli/app.py` delegating to `create_documents_from_opml` and printing JSON output.

## 3. Verification and regression coverage

- [ ] 3.1 Extend `packages/search-core/tests/conftest.py` fixture server with OPML and multi-feed test payloads (including nested outlines and one invalid feed URL).
- [ ] 3.2 Add `packages/search-core/tests/test_ingestion.py` tests for multi-feed OPML ingestion, nested outline discovery, and best-effort partial success.
- [ ] 3.3 Add API and CLI tests (or equivalent integration checks) verifying new OPML route/command behavior and output shape parity with feed ingestion.
