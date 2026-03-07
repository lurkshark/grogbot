## Context

Search currently ranks and returns chunk rows directly. Each result includes both a `document` and a `chunk`, but the returned list is chunk-centered, so the same document can appear multiple times when several chunks from that document score well. The user-facing requirement is to preserve the existing result shape while changing the semantics to document-centered results.

This change affects the shared search core and therefore changes behavior in both the CLI and API. The implementation should avoid heuristic post-processing in Python and instead make unique-document selection part of the SQL query so that `limit` applies to documents deterministically.

## Goals / Non-Goals

**Goals:**
- Return each document at most once from `SearchService.search()`.
- Preserve the current hybrid chunk scoring inputs: FTS, vector similarity, and link score.
- Select a representative chunk per document using SQL-level deduplication.
- Make `limit` count unique documents.
- Preserve the existing `SearchResult` model shape so callers still receive the representative chunk for display.

**Non-Goals:**
- Redesign the scoring formula to aggregate multiple chunks into a new document score.
- Change CLI or API response schemas.
- Introduce new persistence structures, migrations, or background indexing flows.

## Decisions

### Use the highest-ranked chunk as the document representative
The system will continue computing scores at the chunk level, then collapse the scored set to one row per document. The representative chunk will be the highest-ranked chunk for that document by `final_score DESC`, with `chunk_id ASC` as a deterministic tie-breaker.

**Rationale:** This preserves current ranking behavior and keeps the representative snippet grounded in the strongest evidence chunk.

**Alternatives considered:**
- **Python-side dedupe after fetching chunk rows:** rejected because it makes `limit` heuristic and can underfill results when one document dominates many chunk hits.
- **Document-level score aggregation across multiple chunks:** rejected for now because it changes the search model beyond the requested behavior.

### Apply document deduplication in SQL after hybrid scoring
The search query will retain its current hybrid scoring pipeline, produce scored candidate chunks, then use a window function such as `ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY final_score DESC, chunk_id ASC)` to choose one representative chunk per document before the final `LIMIT` is applied.

**Rationale:** SQL-level deduplication makes document uniqueness and limit semantics explicit, deterministic, and testable.

**Alternatives considered:**
- **Deduplicate earlier during FTS/vector candidate generation:** rejected because it could discard the true best chunk before final hybrid scoring.

### Keep SearchResult shape unchanged
`SearchResult` will continue to include both `document` and `chunk`. After this change, the `document` is the primary result entity and `chunk` is the representative snippet for that document.

**Rationale:** This avoids avoidable interface churn while still delivering the desired document-centered behavior.

## Risks / Trade-offs

- **Candidate pool may underfill unique-document results** → If the pre-deduped candidate pool is too small, highly repetitive documents could still reduce the number of unique documents returned. Validate current `candidate_limit` behavior with tests and adjust if needed.
- **Link score still boosts every chunk from the same document before dedupe** → This is acceptable for the requested behavior, but it preserves existing chunk-level fan-out effects in the candidate set.
- **Existing tests are chunk-centered** → Update tests to explicitly cover multi-chunk documents, representative-chunk selection, and document-based limit semantics.

## Migration Plan

- No data migration is required.
- Update search tests first or alongside the query change so the new semantics are locked in.
- Rollback is straightforward: restore the previous chunk-centered query behavior if callers report issues.

## Open Questions

- Whether `candidate_limit = limit * 10` remains sufficient once results are deduplicated to documents should be verified during implementation.
