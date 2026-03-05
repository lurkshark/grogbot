## Why

The SQLite database currently stores full document markdown alongside plaintext chunks, which duplicates large content and increases storage pressure as the corpus grows. We need to keep ingestion efficient while reducing persisted payload size and preserving explicit control over expensive embedding generation.

## What Changes

- **BREAKING** Remove persisted markdown from the `documents` table and `Document` model responses.
- Add compact document change detection via a new `content_hash` field (6-character lowercase hex digest).
- Update document creation/upsert flows to persist document metadata, regenerate outbound links, and regenerate plaintext chunks using the incoming markdown payload, without storing markdown.
- Split vector generation into explicit embedding operations so chunk plaintext creation and embedding persistence are independently triggerable.
- Add single-document and bulk synchronization operations for missing chunk embeddings, mirroring the existing chunk synchronization pattern.
- Update API and CLI surfaces to expose the new embedding operations and return payloads that no longer include full document markdown.

## Capabilities

### New Capabilities
- `document-compact-storage`: Persist document metadata plus a short content hash while dropping stored markdown and regenerating chunk/link data from ingestion inputs.
- `chunk-embedding-sync`: Provide explicit single-document and bulk operations to generate vector rows for chunk plaintext independently of chunk creation.

### Modified Capabilities
- None.

## Impact

- `packages/search-core/src/grogbot_search/service.py` (schema, upsert flow, chunk/link lifecycle, embedding sync methods).
- `packages/search-core/src/grogbot_search/models.py` (document fields).
- `packages/api/src/grogbot_api/app.py` (request/response contracts, new embedding endpoints).
- `packages/cli/src/grogbot_cli/app.py` (new embedding commands, output contract changes).
- Search result serialization and tests that currently rely on `document.content_markdown`.
- Backward compatibility: existing consumers expecting `content_markdown` will need to migrate.
