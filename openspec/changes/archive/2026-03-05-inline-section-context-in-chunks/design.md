## Context

`packages/search-core/src/grogbot_search/chunking.py` currently chunks markdown by section and paragraph, then emits plaintext chunks used by both FTS (`chunks_fts`) and vector embeddings (`chunks_vec`). Current behavior can emit heading-only or weakly contextual chunks, which reduces relevance for section-oriented queries. We want to inline section context directly into chunk text while preserving existing ingestion and search architecture (same schema, same rank-fusion pipeline).

Constraints:
- Keep chunking deterministic and inexpensive.
- Keep compatibility with `SearchService._insert_plaintext_chunks`, which stores a single `content_text` field.
- Maintain existing chunk-size tuning semantics (`TARGET_WORDS`, `MAX_WORDS`) for body text.
- Assume fresh database ingestion (no backfill/migration of existing chunk rows required).

## Goals / Non-Goals

**Goals:**
- Add section-aware context to each emitted chunk by prepending a plain heading path.
- Limit context to top two heading levels to prevent noisy prefixes.
- Keep chunk budget decisions based on body text only.
- Avoid heading-only chunks and avoid mixing multiple section contexts in one chunk.
- Preserve oversized paragraph fallback behavior, with context retained on sentence-based splits.

**Non-Goals:**
- No database schema changes (no separate context column).
- No ranking formula changes in `SearchService.search`.
- No migration workflow for legacy databases.
- No overlap-window chunking redesign in this change.

## Decisions

1. **Inline context in `content_text` with no marker**
   - Decision: Prepend plain context text in `H1 > H2` form (or single heading when only one level exists), followed by body content.
   - Rationale: Works immediately with existing FTS + embedding pipeline and avoids schema/search changes.
   - Alternatives considered:
     - Context marker like `[CTX] ...`: rejected to reduce lexical noise and formatting overhead.
     - Separate context column: rejected for this change due to schema and query complexity.

2. **Context source is heading stack truncated to top 2 levels**
   - Decision: Build context from active markdown heading hierarchy, keeping only first two levels.
   - Rationale: Keeps high-signal topic labels while avoiding long/deep heading paths.
   - Alternatives considered:
     - Deepest two levels: can drop broad domain context.
     - Full hierarchy: higher noise and repeated text.

3. **Chunk budgeting excludes context words**
   - Decision: `TARGET_WORDS`/`MAX_WORDS` calculations use body words only.
   - Rationale: Preserves current chunk-size behavior and avoids shrinking body payload for long headings.
   - Alternatives considered:
     - Include context in budget: simpler accounting but unstable body capacity.

4. **Flush on context change and suppress heading-only output**
   - Decision: When heading path changes, flush active body chunk before accumulating blocks under the new context. Do not emit chunks containing only headings.
   - Rationale: Prevents mixed-topic chunks and removes low-value fragments.
   - Alternatives considered:
     - Allow mixed-context chunks until size threshold: risks ambiguous retrieval matches.

5. **Sentence fallback keeps inherited context**
   - Decision: If a body block exceeds `MAX_WORDS`, split by sentence groups as today and prepend the same context to each emitted chunk.
   - Rationale: Preserves oversized-content handling while maintaining topic cues.
   - Alternatives considered:
     - Drop context for fallback chunks: creates inconsistent retrieval behavior.

## Risks / Trade-offs

- **[Risk] Context text dominates short-body chunks** → **Mitigation:** cap depth at two levels and avoid heading-only chunks.
- **[Risk] Plain prefix may alter lexical scoring distribution** → **Mitigation:** validate with focused retrieval tests (heading-term and body-term queries).
- **[Risk] Regex sentence splitting remains imperfect for abbreviations/edge punctuation** → **Mitigation:** preserve existing behavior in this change and isolate improvements for a follow-up.
- **[Trade-off] No marker means less explicit machine parsing** → **Mitigation:** deterministic prefix format (`H1 > H2`) keeps behavior predictable for tests.

## Migration Plan

- Fresh-ingest assumption means no data migration is needed.
- Rollout consists of deploying updated chunking logic, then ingesting documents into a new database.
- Rollback is straightforward: deploy previous chunking logic and re-ingest into a fresh database.

## Open Questions

- Should extremely generic headings (for example, "Overview") be filtered from context in a follow-up?
- Should future work add optional overlap windows after context inlining quality is measured?
