## 1. Schema and model updates

- [x] 1.1 Replace `documents.content_markdown` with `documents.content_hash` in schema initialization and add DB-level 6-char lowercase-hex constraints.
- [x] 1.2 Implement startup migration for legacy databases that rebuilds `documents` and backfills `content_hash` from prior markdown values.
- [x] 1.3 Update `Document` model and related serialization/query mapping to remove `content_markdown` and include `content_hash`.

## 2. Document upsert and ingestion flow refactor

- [x] 2.1 Update `upsert_document` to compute `content_hash` from incoming markdown and persist metadata + hash.
- [x] 2.2 Regenerate plaintext chunks and outbound links during upsert for new documents or changed hashes, while preserving existing chunks/links on unchanged hashes.
- [x] 2.3 Ensure ingestion helpers (`create_document_from_url`, feed/opml/sitemap ingestion) continue to pass markdown input but no longer rely on persisted markdown.

## 3. Separate embedding lifecycle operations

- [x] 3.1 Refactor chunk creation helpers to support plaintext chunk insertion without immediate vector writes.
- [x] 3.2 Add single-document embedding operation that generates missing vector rows for one document and returns vectors created.
- [x] 3.3 Add bulk embedding synchronization operation over documents with missing vectors, with optional `maximum` and stable ordering.
- [x] 3.4 Expose embedding operations through API routes and CLI commands with consistent response payloads (`vectors_created`).

## 4. Search path, compatibility, and validation

- [x] 4.1 Update search result hydration and any document fetch/list paths to align with the new document shape (no markdown field).
- [x] 4.2 Add/adjust tests for schema migration, hash-based upsert behavior, chunk/link regeneration rules, and embedding sync operations.
- [x] 4.3 Add/adjust API and CLI tests for embedding endpoints/commands and breaking output contract changes.
- [x] 4.4 Update README or user-facing docs to describe the new embedding workflow and removed `content_markdown` field.
