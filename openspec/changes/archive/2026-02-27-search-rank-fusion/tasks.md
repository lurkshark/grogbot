## 1. Implement reciprocal-rank fusion query logic

- [x] 1.1 Replace the current weighted hybrid scoring path in `packages/search-core/src/grogbot_search/service.py` with rank-fusion logic.
- [x] 1.2 Update FTS candidate retrieval to use top `limit * 10` rows ordered by `bm25(chunks_fts)` ascending with deterministic `chunk_id` tie-breaking.
- [x] 1.3 Update vector candidate retrieval to use top `limit * 10` rows ordered by `distance` ascending with deterministic `chunk_id` tie-breaking.
- [x] 1.4 Compute per-method scores using reciprocal row numbers (`1.0 / (1 + row_number)`) and final score as additive fusion (`fts_score + vector_score`).
- [x] 1.5 Ensure final ranking returns top `limit` chunks by descending final score while preserving `fts_score` and `vector_score` in results.

## 2. Validate and document new ranking behavior

- [x] 2.1 Update/add unit tests in `packages/search-core/tests/test_service.py` to cover candidate depth, deterministic ordering, reciprocal scoring, and additive final scoring.
- [x] 2.2 Update user/developer-facing wording that still describes weighted blend semantics (if present) to reflect reciprocal-rank fusion behavior.
- [x] 2.3 Run search-core test suite and confirm all tests pass with the new ranking implementation.
