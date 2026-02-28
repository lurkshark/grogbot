## Why

Users can currently ingest a single feed URL at a time, which makes onboarding existing feed subscriptions slow and manual. Supporting OPML URL ingestion enables bulk import from standard feed-reader export files and reduces setup friction.

## What Changes

- Add a new service-layer API `create_documents_from_opml(opml_url)` that fetches and parses an OPML document.
- Extract feed URLs from nested OPML outlines (`xmlUrl`) and ingest each feed via existing `create_documents_from_feed`.
- Use best-effort ingestion: continue processing remaining feeds when one feed fails.
- Return a flat `List[Document]` to keep parity with existing feed-ingestion behavior.
- Add a new API endpoint for OPML ingestion.
- Add a new CLI command for OPML ingestion.

## Capabilities

### New Capabilities
- `opml-ingestion`: Bulk-ingest documents from an OPML URL by iterating feed URLs and delegating each feed to existing feed ingestion, exposed consistently in core service, API, and CLI.

### Modified Capabilities
- *(none)*

## Impact

- **Search core**: `packages/search-core/src/grogbot_search/service.py` gains OPML orchestration logic.
- **API**: `packages/api/src/grogbot_api/app.py` gains OPML ingest request model and route.
- **CLI**: `packages/cli/src/grogbot_cli/app.py` gains `search ingest-opml` command.
- **Tests**: Add ingestion tests for nested outline handling and best-effort partial success.
- **Dependencies**: Likely add an OPML/XML parser dependency (or implement with stdlib XML parsing).
