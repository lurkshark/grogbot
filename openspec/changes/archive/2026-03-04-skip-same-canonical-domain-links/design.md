## Context

The link graph is populated during `chunk_document(document_id)` by extracting markdown links and persisting unique `(from_document_id, to_document_id)` edges. Current filtering excludes self-links but still records links between different documents on the same canonical domain, which can over-amplify intra-site structures in the link-based ranking signal.

This change is constrained to search-core link extraction and tests. No schema change is required.

## Goals / Non-Goals

**Goals:**
- Persist outbound edges only when source and target canonical domains differ.
- Treat relative outbound links as same-domain by resolving against the source document canonical URL before filtering.
- Preserve existing behavior for dedupe, unknown target handling (`document_id_for_url`), and lifecycle refresh semantics.
- Update tests so link graph and ranking assertions reflect cross-domain-only edge persistence.

**Non-Goals:**
- Redefining canonical domain normalization (`netloc` remains the canonical domain key).
- Changing DB schema or link table shape.
- Introducing weighting by domain category or any other ranking formula changes beyond input edge set.

## Decisions

1. **Apply domain filtering in URL-to-target derivation before insertion**
   - Decision: Extend the outbound link derivation helper to accept the source document canonical URL and skip targets whose normalized domain equals the source domain.
   - Rationale: Keeps filtering in one place with self-link exclusion and dedupe, minimizing lifecycle-path drift.
   - Alternative considered: Filter at SQL insert time by joining source document data per edge; rejected as more complex and less explicit for relative-link handling.

2. **Resolve relative links against source canonical URL for domain checks**
   - Decision: Use `urljoin(source_canonical_url, href)` prior to canonicalization/domain extraction when deriving targets.
   - Rationale: Ensures internal relative links are consistently treated as same-domain and skipped.
   - Alternative considered: Ignore relative links entirely; rejected because it changes existing link extraction semantics and may drop legitimate cross-domain absolute forms in mixed content.

3. **Keep unknown-target behavior unchanged after filtering**
   - Decision: After passing domain filter, derive `to_document_id` via `document_id_for_url(_canonicalize_url(resolved_url))` even if no target document exists.
   - Rationale: Preserves current contract and avoids coupling to ingestion state.
   - Alternative considered: Require target documents to exist before storing edges; rejected as scope creep and behavior regression.

4. **Refactor tests to explicit multi-domain fixtures**
   - Decision: Update link graph and link-score tests that currently rely on same-domain edges to use at least two domains.
   - Rationale: Makes expectations align with the new rule and prevents accidental reliance on intra-domain edge persistence.
   - Alternative considered: Keep same fixtures and loosen assertions; rejected because it obscures intended behavior.

## Risks / Trade-offs

- **[Risk] `netloc`-based equality treats `www.example.com` and `example.com` as different domains** → **Mitigation:** Preserve current canonical-domain contract for now; document behavior in spec scenarios and revisit in a separate normalization change if needed.
- **[Risk] Relative-link resolution may expose malformed markdown href values** → **Mitigation:** Continue canonicalization and skip empty/unusable URLs; maintain deterministic helper-level filtering.
- **[Risk] Fewer stored edges may reduce link-score differentiation on single-site corpora** → **Mitigation:** Intentional trade-off to avoid intra-site self-reinforcement; ranking still uses FTS/vector signals.

## Migration Plan

1. Update link-derivation helper signature and call sites to include source canonical URL.
2. Implement same-domain skip with relative-link resolution.
3. Update unit tests for link persistence/lifecycle and ranking expectations.
4. Run test suite and verify no API/CLI contract changes.

Rollback: revert helper/filter changes and corresponding test updates; schema remains unchanged so rollback is code-only.

## Open Questions

- None for this iteration.
