## Why

Chunking currently happens inside `upsert_document`, which couples document writes to embedding work and makes ingestion paths slower and less controllable. Separating chunking allows us to defer heavy processing, re-run indexing explicitly, and add batch maintenance commands.

## What Changes

- Split document upsert from chunking so `upsert_document` only writes documents and (when content changes) deletes existing chunks.
- Prevent creation of documents with empty `content_markdown` (ingestion/upsert validation).
- Add a chunking service method that accepts a document id, reloads the document, clears existing chunks, and recreates chunks/embeddings.
- Add a bulk chunking service method to process documents without chunks, with an optional maximum count.
- Expose single-document and bulk chunking via API endpoints and CLI commands.
- Update ingestion helpers and tests to invoke chunking explicitly rather than implicitly.

## Capabilities

### New Capabilities
- `document-chunking`: Manage chunk generation independently of document upserts, including single-document and bulk chunk creation workflows.

### Modified Capabilities
- (none)

## Impact

- `packages/search-core/src/grogbot_search/service.py` (upsert behavior, new chunking methods).
- API routes and request/response handling in `packages/api/src/grogbot_api/app.py`.
- CLI commands in `packages/cli/src/grogbot_cli/app.py`.
- Tests that rely on chunks/search results.
- Ingestion helpers now leave documents unchunked until chunking is triggered.
