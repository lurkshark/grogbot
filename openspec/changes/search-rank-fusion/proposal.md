## Why

The current hybrid ranking blends normalized FTS and vector distance scores with fixed weights, which makes ordering sensitive to score scale differences and can produce unintuitive results. We need a rank-based fusion method that is stable, deterministic, and directly controlled by the requested result limit.

## What Changes

- Replace weighted hybrid scoring in query search with rank-fusion scoring based on reciprocal row numbers.
- Select FTS candidates from the top `limit * 10` rows ordered by `bm25(chunks_fts)` ascending.
- Select vector candidates from the top `limit * 10` rows ordered by `distance` ascending.
- Assign `row_number()` independently to each candidate set (ordered by rank/distance ascending, then `chunk_id` ascending for deterministic tie-breaking).
- Compute per-method scores as `1.0 / (1 + row_number)` and set final chunk score to `fts_score + vector_score`.
- Return final results ordered by final score descending, limited to `limit`.

## Capabilities

### New Capabilities
- `search-rank-fusion`: Defines reciprocal-rank fusion behavior for combining FTS and vector candidates in search.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/search-core/src/grogbot_search/service.py` search query and scoring flow.
- Affected tests: `packages/search-core/tests/test_service.py` for ranking/scoring expectations.
- External APIs remain unchanged (`search(query, limit)` and CLI/API query interfaces), but result ordering semantics will change.
- No new runtime dependencies expected.
