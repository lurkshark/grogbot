## Context

Search ranking currently fuses two chunk-level retrieval streams (FTS and vector) using reciprocal row-number scoring. The system has no graph signal for document authority, even though ingested markdown often contains outbound links. We need a lightweight page-rank-style signal where documents linked by more distinct source documents receive better rank.

Existing behavior already separates document upsert from chunking: content changes delete chunks, and `chunk_document(document_id)` regenerates chunks. This change should align link lifecycle with that same pattern.

Constraints:
- Link identity is exactly `(from_document_id, to_document_id)` with no per-link count.
- Multiple links from one document to the same target collapse to one edge.
- Outbound links from a document must be cleared when content changes or when document is deleted.
- Link extraction should run as part of `chunk_document`.
- Search must expose `link_score` and treat it as equal-weight to FTS and vector scores.
- Documents with zero inbound links must have `link_score = 0.0`.

## Goals / Non-Goals

**Goals:**
- Add persistent link graph storage with uniqueness by `(from,to)`.
- Keep links in sync with document lifecycle (content change/delete/chunk regenerate).
- Derive `to_document_id` for unknown targets using `_canonicalize_url` + `document_id_for_url`.
- Add a third reciprocal-rank search signal (`link_score`) with equal additive weight.
- Return `link_score` in `SearchResult` payloads.

**Non-Goals:**
- Implement iterative/global PageRank or damping-factor graph algorithms.
- Track per-link multiplicity within one source document.
- Add new API endpoints for direct link CRUD.
- Change query endpoint/CLI shape beyond additional `link_score` field in results.

## Decisions

1. **Store links in a dedicated `links` table keyed by `(from_document_id, to_document_id)`**
   - Decision: Add table:
     - `from_document_id TEXT NOT NULL`
     - `to_document_id TEXT NOT NULL`
     - `PRIMARY KEY (from_document_id, to_document_id)`
     - `FOREIGN KEY (from_document_id) REFERENCES documents(id) ON DELETE CASCADE`
     - index on `to_document_id`
   - Rationale: Enforces one edge per source-target pair and supports efficient inbound counting.
   - Alternative considered: `id` surrogate plus unique index; rejected as unnecessary complexity.

2. **Extract outbound links during `chunk_document` and fully refresh per source document**
   - Decision: In `chunk_document(document_id)`, delete existing outbound links for `document_id`, then extract links from `document.content_markdown`, dedupe targets, ignore self-links, and insert with `INSERT OR IGNORE`.
   - Rationale: Mirrors chunk regeneration semantics and guarantees graph consistency with current content.
   - Alternative considered: extract during `upsert_document`; rejected because chunking is already the indexing boundary.

3. **Clear outbound links when document content changes**
   - Decision: In `upsert_document`, when `content_changed` is true, delete both chunks and outbound links for that document before commit.
   - Rationale: Prevents stale link edges between upsert and next chunk run.
   - Alternative considered: only clear on next `chunk_document`; rejected because stale links would affect ranking in the interim.

4. **Treat unknown targets as first-class link destinations**
   - Decision: For each extracted href, compute `target_url = _canonicalize_url(href)` and `to_document_id = document_id_for_url(target_url)` even if no matching `documents` row exists.
   - Rationale: Preserves graph evidence ahead of ingestion order and matches requested behavior.
   - Alternative considered: only store links to known documents; rejected by requirement.

5. **Compute link signal as query-time reciprocal rank over candidate documents with inbound links**
   - Decision: In `search`, add CTEs to:
     - map candidate chunks to candidate documents,
     - count inbound edges per candidate document (`COUNT(*)` on distinct `(from,to)` table rows),
     - rank only documents with inbound count > 0 by `inbound_count DESC, document_id ASC`,
     - compute `link_score = 1.0 / (1 + row_number)`,
     - `COALESCE(link_score, 0.0)` for documents with zero inbound links.
   - Rationale: Keeps scoring query-local, deterministic, and directly combinable with existing reciprocal FTS/vector channels.
   - Alternative considered: global precomputed link ranks; rejected for additional complexity and staleness management.

6. **Expose `link_score` in the public search model**
   - Decision: Extend `SearchResult` with a required `link_score: float` and populate it in `SearchService.search`.
   - Rationale: Required for transparency and downstream tuning/inspection.
   - Alternative considered: keep link score internal to `score`; rejected by requirement.

## Risks / Trade-offs

- **[Risk] Relative/fragment links may map to hashed IDs that never resolve cleanly** → **Mitigation:** canonicalize uniformly and accept unknown targets; behavior remains deterministic and non-blocking.
- **[Risk] Additional SQL CTE/join complexity may affect query latency** → **Mitigation:** keep candidate pool bounded (`limit * 10`), index `links.to_document_id`, and validate via test coverage.
- **[Risk] Query-local link ranking means scores are relative to candidate set, not global authority** → **Mitigation:** intentional for equal-weight reciprocal fusion; revisit with global precompute only if relevance data demands it.
- **[Risk] Stale links if ingestion writes content but chunking is deferred indefinitely** → **Mitigation:** content-change path clears outbound links immediately; synchronization jobs can rebuild when needed.

## Migration Plan

1. Add `links` table/index in `_init_schema` (idempotent `CREATE TABLE/INDEX IF NOT EXISTS`).
2. Update link lifecycle in `upsert_document`, `chunk_document`, and delete behavior (via FK cascade on `from_document_id`).
3. Add outbound link extraction + insertion helper(s) used by `chunk_document`.
4. Extend search SQL and `SearchResult` model with `link_score`.
5. Update tests for link persistence/lifecycle and three-signal fusion semantics.
6. Rollback path: remove link-score CTE integration and `link_score` model field while leaving table unused (safe backward rollback without destructive migration).

## Open Questions

- None.