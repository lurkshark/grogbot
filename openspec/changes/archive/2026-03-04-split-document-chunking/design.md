## Context

Chunk creation is currently embedded in `SearchService.upsert_document`, which means any document write also performs chunking and embedding. This couples ingestion latency to embedding cost and makes re-chunking or batch chunking hard to control. The change needs to separate document persistence from chunk generation while keeping chunk deletion on content change.

## Goals / Non-Goals

**Goals:**
- Make `upsert_document` write-only for documents, deleting existing chunks only when content changes.
- Reject empty document content before persistence to avoid permanent chunkless records.
- Provide explicit chunking operations (single-document and bulk) that return created chunk counts.
- Expose the chunking operations through API and CLI.
- Keep chunking logic centralized around existing `_create_chunks` helper.

**Non-Goals:**
- Changing chunking algorithms, embeddings, or database schema.
- Introducing background workers or async processing.
- Defining new ingestion sources beyond the current URL/feed/sitemap/opml helpers.

## Decisions

- **Create explicit chunking service methods**: Add `chunk_document(document_id)` and `synchronize_document_chunks(maximum=None)` to `SearchService` rather than reusing `upsert_document`. This makes chunk generation explicit and reusable for API/CLI.
  - *Alternative:* Add a flag to `upsert_document` to skip chunking. Rejected to avoid complicating the upsert API and mixing responsibilities.
- **Reject empty document content**: Validate `content_markdown` is non-empty (after trimming) before inserting or updating a document, including ingestion helpers. This prevents persistent chunkless documents from empty content.
  - *Alternative:* Allow empty documents and skip chunking. Rejected to avoid repeatedly selecting chunkless documents and to keep search data meaningful.
- **Return chunk counts**: Both chunking methods return an integer count of chunks created. This keeps API/CLI responses minimal and avoids returning potentially large chunk payloads.
  - *Alternative:* Return created chunks for richer information. Rejected to keep responses lightweight and to avoid embedding large text in API outputs.
- **Stable bulk ordering by document id**: Bulk chunking will select documents with no chunks ordered by `documents.id` (or equivalent stable field). This supports reproducibility without introducing new ordering requirements.
- **Reuse `_create_chunks` as the single chunking implementation**: The public chunking method will fetch the document, clear chunks, then call `_create_chunks` with the stored markdown.

## Risks / Trade-offs

- **Search results missing until chunking is run** → Ensure ingestion paths and tests explicitly call chunking after upserts; document the change in API/CLI.
- **Chunkless documents remain if chunking fails** → Bulk chunking can be re-run; failures should not block processing of other documents.

## Migration Plan

- No schema migrations required.
- Existing chunks remain untouched for unchanged documents.
- After deploy, re-run bulk chunking to backfill any chunkless documents created by the new flow.

## Open Questions

- None at this time.
