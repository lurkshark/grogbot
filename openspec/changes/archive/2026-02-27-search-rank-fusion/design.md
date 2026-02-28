## Context

Search currently computes a hybrid score by blending normalized FTS scores and inverse-distance vector scores with fixed weights (0.7/0.3). This approach mixes heterogeneous score scales and requires normalization logic that is sensitive to candidate distribution per query. The requested change replaces this with a rank-based fusion algorithm where each retrieval method contributes based on candidate position rather than raw score magnitude.

Constraints:
- Keep existing query API shape unchanged (`search(query, limit)`).
- Use existing SQLite FTS5 and sqlite-vec tables.
- Preserve deterministic ordering for ties.

## Goals / Non-Goals

**Goals:**
- Replace weighted blending with reciprocal row-number fusion.
- Use `limit * 10` as candidate pool size for both FTS and vector retrieval.
- Compute method scores as `1.0 / (1 + row_number)` where `row_number` starts at 1.
- Combine scores with simple addition and rank by descending total.
- Keep per-result `fts_score` and `vector_score` fields populated using the new method.

**Non-Goals:**
- Changing chunking, embedding generation, or schema layout.
- Introducing query-time personalization or additional ranking signals.
- Modifying external CLI/API contracts.

## Decisions

1. **Use SQL window functions for ranking in each retrieval stream**
   - Decision: Use `row_number() OVER (ORDER BY ...)` for FTS and vector candidates independently.
   - Rationale: This directly expresses the intended ranking logic, avoids Python-side re-ranking bugs, and keeps deterministic tie handling in SQL.
   - Alternative considered: Rank in Python after fetching rows; rejected because SQL window functions are clearer and less error-prone.

2. **Use identical candidate depth for both methods (`limit * 10`)**
   - Decision: Retrieve top `limit * 10` rows for FTS and vector candidates.
   - Rationale: Matches requested behavior and gives each method enough headroom to contribute overlapping and non-overlapping chunks.
   - Alternative considered: Different multipliers per method; rejected to keep behavior predictable and symmetric.

3. **Use reciprocal row score with floating-point division**
   - Decision: Score as `1.0 / (1 + row_number)`.
   - Rationale: Produces monotonic decay by rank position and prevents integer truncation in SQLite.
   - Alternative considered: Distance-based reciprocal for vector only; rejected because objective is unified rank-fusion.

4. **Final score is additive with zero fill for missing channels**
   - Decision: `final = coalesce(fts_score, 0.0) + coalesce(vector_score, 0.0)`.
   - Rationale: Ensures chunks retrieved by only one method still rank, while overlap across methods is rewarded.
   - Alternative considered: Keep weighted blend; rejected per scope.

## Risks / Trade-offs

- **[Risk] Lower sensitivity to raw score magnitude** → **Mitigation:** This is intentional for stability; validate result quality with targeted tests and sample queries.
- **[Risk] SQL complexity increases with CTE/window usage** → **Mitigation:** Keep query segmented into named CTEs and add tests for deterministic output.
- **[Risk] Runtime impact from larger candidate pools (`limit * 10`)** → **Mitigation:** Candidate cap is still bounded and tied to user-supplied `limit`; monitor query latency.

## Migration Plan

- Implement ranking query and scoring replacement in `SearchService.search`.
- Update/extend tests to assert new scoring semantics and ordering.
- No schema migration required.
- Rollback path: restore previous weighted scoring block if behavior regressions are detected.

## Open Questions

- None at this time; row-number origin, tie-breaker, and blend replacement are all resolved.
