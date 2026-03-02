## Why

Some RSS/Atom feeds expose pagination via `<link rel="next">`, so ingesting only the first page misses historical entries. We need an optional pagination mode to traverse these feeds when desired.

## What Changes

- Add an optional `paginate` flag (default `False`) to `SearchService.create_documents_from_feed` that follows `<link rel="next">` up to 100 pages.
- Add an optional `paginate` flag (default `False`) to `SearchService.create_documents_from_opml` and pass through to feed ingestion.
- Extend the feed ingest API/CLI to accept a `paginate` boolean option.
- Update CLI bootstrap to call feed ingestion with `paginate=True`.
- Pagination is best-effort: failures on later pages stop pagination without erroring the already-ingested results.

## Capabilities

### New Capabilities
- `feed-pagination`: Optional pagination for RSS/Atom feed ingestion using `<link rel="next">` with a 100-page cap.

### Modified Capabilities
- (none)

## Impact

- `packages/search-core/src/grogbot_search/service.py` (feed/opml ingestion behavior)
- `packages/api/src/grogbot_api/app.py` (feed ingest request schema)
- `packages/cli/src/grogbot_cli/app.py` (ingest-feed and bootstrap behavior)
- Tests for ingestion pagination
