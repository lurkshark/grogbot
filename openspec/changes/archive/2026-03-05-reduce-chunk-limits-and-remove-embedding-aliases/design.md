## Context

Bulk embedding synchronization is failing on Apple MPS with out-of-memory errors. The current chunking bounds permit large chunk text payloads, which increases per-encode memory pressure even at low batch sizes. In this codebase, chunking and embedding are already decoupled, so reducing chunk-size bounds is a focused way to lower embedding-time risk without changing model or ranking behavior.

The search service also retains legacy backward-compatible alias methods (`chunk_document`, `synchronize_document_chunks`) that duplicate canonical embedding methods and expand the maintained API surface.

## Goals / Non-Goals

**Goals**
- Reduce chunk-size bounds to lower worst-case embedding memory usage on MPS.
- Keep chunking algorithm behavior the same except for new bounds.
- Remove deprecated alias methods in `SearchService` and standardize callers on canonical embedding method names.

**Non-Goals**
- Changing embedding model, embedding batch size defaults, or device selection.
- Introducing rechunk migration for existing persisted corpora.
- Altering rank-fusion or search scoring behavior.

## Decisions

1. **Set chunk bounds to 512/1024 words**
   - Decision: `TARGET_WORDS = 512`, `MAX_WORDS = 1024`.
   - Rationale: materially lowers per-call sequence size while preserving enough context per chunk.
   - Alternative considered: 256/512; rejected for now to avoid excessive chunk proliferation and retrieval fragmentation.

2. **Retain current chunking mechanics**
   - Decision: keep section/paragraph/sentence splitting and flush logic unchanged.
   - Rationale: isolates risk reduction to chunk-size bounds and avoids introducing new algorithm behavior.

3. **Remove compatibility aliases from service layer**
   - Decision: delete `chunk_document` and `synchronize_document_chunks` aliases.
   - Rationale: canonical embedding methods already exist and are used by CLI/API; aliases add maintenance burden and ambiguity.
   - Alternative considered: keep aliases with deprecation warnings; rejected to complete API cleanup in one breaking change.

## Risks / Trade-offs

- **[Trade-off] More chunks per document** → Increased storage rows and potential query fan-out.
- **[Risk] Retrieval quality shifts due to smaller chunk windows** → Validate key query behavior in tests and manual spot checks.
- **[Risk] Internal callers/tests still using aliases** → Update all usages in same change and fail fast if missed.

## Migration Plan

- No data migration is required in this change.
- Operational assumption: database is empty and content will be re-ingested after deployment.
- Remove aliases and update test/docs references in the same release so no mixed internal API usage remains.

## Open Questions

- None currently.
