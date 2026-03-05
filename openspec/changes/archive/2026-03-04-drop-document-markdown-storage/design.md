## Context

The current search-core persistence model stores full markdown in `documents.content_markdown` and also stores plaintext chunk content in `chunks.content_text`. This duplicates large payloads and increases SQLite file size over time. The current `chunk_document` and `synchronize_document_chunks` operations also couple chunk regeneration with embedding generation, which makes expensive vector work harder to control independently.

This change needs to preserve ingestion behavior (document metadata + link graph + chunk plaintext) while moving vector creation into a separate explicit phase. Existing API/CLI consumers currently receive `Document.content_markdown`, so this is an intentional breaking contract change.

## Goals / Non-Goals

**Goals:**
- Remove persisted markdown copies from documents.
- Add compact content change detection with `content_hash` as a 6-character lowercase hex digest.
- Make document upsert/ingest persist metadata and regenerate chunks/links without running embeddings.
- Add explicit embedding operations (single-document and bulk sync) that mirror current chunk sync ergonomics.
- Keep search behavior stable by continuing to read plaintext chunks from `chunks` and vectors from `chunks_vec`.

**Non-Goals:**
- Changing chunking heuristics, embedding model, or rank-fusion formulas.
- Introducing async/background workers.
- Adding new ingestion source types.

## Decisions

1. **Replace `documents.content_markdown` with `documents.content_hash`**
   - Decision: Store a 6-character lowercase hex digest derived from incoming markdown content.
   - Rationale: Enables fast change detection without storing full markdown text.
   - Constraint: Enforce shape at the DB layer (`length = 6`, lowercase hex only).
   - Alternative considered: keep full markdown plus hash; rejected because it does not reduce primary storage pressure.

2. **Regenerate chunks and links inside document upsert when content changes**
   - Decision: `upsert_document` receives markdown input, computes hash, and if changed (or new doc), clears existing chunks/links and recreates plaintext chunks and outbound links immediately.
   - Rationale: Keeps chunk/link data current without requiring a follow-up operation and aligns with requested document creation behavior.
   - Alternative considered: leave chunk regeneration as a separate call; rejected because requested flow requires document + links + plaintext chunks at creation/upsert time.

3. **Split embeddings into dedicated operations**
   - Decision: Add explicit methods for embedding generation (single document + bulk sync for missing vectors).
   - Rationale: Embeddings are resource intensive and should be independently controllable like current chunk sync workflows.
   - Alternative considered: keep embeddings in `chunk_document`; rejected because it preserves current coupling and does not satisfy resource-control goals.

4. **Define embedding sync by missing vector rows, not by chunkless documents**
   - Decision: Bulk embedding sync selects chunks/documents where chunks exist but corresponding `chunks_vec` rows are missing.
   - Rationale: Embedding state is now independent; chunk existence alone is insufficient.
   - Alternative considered: always re-embed all chunks for selected documents; rejected due to unnecessary compute and cost.

5. **Migrate existing databases via table rebuild + backfill hash**
   - Decision: Add a schema migration path that rebuilds `documents` to new columns and backfills `content_hash` from old `content_markdown` values before dropping markdown storage.
   - Rationale: Preserves existing corpus while transitioning storage layout.
   - Alternative considered: destructive reset; rejected because it would force complete re-ingestion.

## Risks / Trade-offs

- **[Risk] 6-hex hash collisions can suppress needed chunk/link refreshes** → **Mitigation:** accept as an explicit compactness trade-off; scope is local corpus, and operators can force refresh by re-upserting with a changed hash input pattern if ever needed.
- **[Risk] No stored markdown prevents offline re-chunking from DB alone** → **Mitigation:** accepted product trade-off; re-chunking requires re-ingestion from source content.
- **[Risk] Breaking API/CLI contract for `Document.content_markdown`** → **Mitigation:** mark as BREAKING in proposal/specs and update response models/docs in the same change.
- **[Risk] Migration complexity around legacy schema** → **Mitigation:** implement deterministic startup migration with transactional table swap and tests over pre-migration fixtures.

## Migration Plan

1. Detect legacy `documents` schema containing `content_markdown` and missing `content_hash`.
2. Create replacement `documents` table with new shape and constraints.
3. Copy rows from old table into new table while computing `content_hash` from legacy markdown (`sha256(markdown)[:6]`).
4. Swap tables atomically in a transaction and recreate dependent indexes/foreign keys.
5. Keep existing chunks/links/vectors intact; future upserts maintain hash/chunks/links and embedding sync handles vectors.
6. Rollback strategy: restore from SQLite backup file if migration fails before commit.

## Open Questions

- None currently.
