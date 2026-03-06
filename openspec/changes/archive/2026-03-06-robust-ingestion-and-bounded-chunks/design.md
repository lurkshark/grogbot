## Context

The current search ingestion pipeline converts extracted HTML directly into markdown and then chunks markdown-derived plaintext with only section/paragraph/sentence heuristics. This works for normal article prose, but it remains fragile when extraction returns malformed markup, giant generator-style lists, embedded widget output, or low-signal text blobs. Those inputs can survive into persisted chunk rows and later produce large embedding-time memory spikes on Apple MPS.

The intended search experience is prose-oriented: we care most about well-formed natural-language sentences, section context, and useful outbound links. We are explicitly willing to drop noisy or non-prose content if doing so improves retrieval quality and operational stability. We can also assume a full re-ingest, so the design does not need to preserve compatibility with previously persisted chunks.

## Goals / Non-Goals

**Goals:**
- Bound every emitted chunk with true hard safety limits, even when extracted content is malformed or punctuation-poor.
- Improve ingestion quality by aggressively removing low-signal or non-content artifacts before chunk creation.
- Preserve useful outbound links independently from prose-pruning decisions.
- Keep the current local-first architecture (Readability/feed parsing → markdown/plaintext → SQLite/FTS/vector search) while making it more robust.
- Reduce embedding-time memory risk without changing the embedding model or rank-fusion approach.

**Non-Goals:**
- Migrating or rechunking existing persisted corpora in place.
- Preserving every table, generator output, or machine-produced list for search.
- Changing ranking formulas, storage schema for search results, or the embedding provider/model.
- Introducing site-specific scraping rules or a full tokenizer-based chunking pipeline.

## Decisions

1. **Add a shared ingestion hygiene stage before chunk persistence**
   - Decision: both URL ingestion and feed ingestion will pass extracted HTML/content through a common cleanup pipeline before markdown/plaintext is derived.
   - Rationale: the same failure modes appear in both page extraction and feed entry content; a shared path keeps behavior consistent and testable.
   - Alternative considered: keep separate cleanup logic per ingestion source. Rejected because it duplicates heuristics and invites drift.

2. **Be aggressively prose-biased during cleanup**
   - Decision: sanitize extracted HTML to remove obviously non-content elements (scripts, styles, embedded widgets, forms, navigation/aside/footer-like fragments, unsafe hrefs, comments, empty wrappers) and normalize text aggressively (Unicode normalization, whitespace collapse, removal of control/zero-width junk).
   - Rationale: the system’s value comes from indexing readable prose and links, not faithfully preserving every extracted byte.
   - Alternative considered: minimal cleanup plus downstream chunk splitting only. Rejected because it still persists junk and wastes embedding/storage capacity.

3. **Separate link preservation from prose filtering**
   - Decision: extract outbound links from cleaned source HTML before aggressive prose-quality filtering, and keep link extraction logically separate from the text-chunk path.
   - Rationale: useful links should survive even when surrounding text is dropped as low-signal.
   - Alternative considered: continue deriving links only from persisted markdown/text. Rejected because stronger text pruning would unintentionally remove valuable graph edges.

4. **Introduce multi-stage fallback chunk splitting with hard guarantees**
   - Decision: retain section/context-aware chunking for normal content, but when a block exceeds the configured safety bounds, split progressively by sentence, then by line/list-like boundaries or other simple delimiters, then by fixed word windows, and finally by character windows if needed.
   - Rationale: semantic grouping remains preferable for normal prose, but robustness requires a final guarantee that no emitted chunk exceeds absolute bounds.
   - Alternative considered: switch entirely to fixed token windows. Rejected because it adds tokenizer coupling and reduces readability/semantic coherence more than necessary.

5. **Gate chunk emission with explicit quality checks**
   - Decision: chunks/blocks that remain low-signal after cleanup may be dropped instead of force-embedding them. Signals may include extreme repetition, very low alphabetic density, very low sentence density, pathological long-token patterns, or other clear indicators of non-prose content.
   - Rationale: dropping junk is preferable to embedding content that harms retrieval and operational stability.
   - Alternative considered: force-split and embed every surviving block. Rejected because it preserves precisely the content class we want to de-emphasize.

6. **Keep word-based chunk targets, but add an additional hard non-word safety bound**
   - Decision: preserve the current word-oriented chunking posture for semantic grouping, while also enforcing an absolute secondary bound (for example, by character length) so unusually token-dense or malformed text cannot bypass safety via word counting alone.
   - Rationale: word count is a useful retrieval heuristic, but it is not a sufficient guardrail against model memory spikes.
   - Alternative considered: rely only on word limits. Rejected because pathological Unicode or punctuation-free text can still create oversized model inputs.

## Risks / Trade-offs

- **[Trade-off] More chunks per corpus** → Accept higher chunk counts in exchange for safer embedding behavior and cleaner retrieval inputs.
- **[Risk] Useful structured content may be dropped** → Bias heuristics toward preserving readable short list items and headings; validate with representative manual spot checks.
- **[Risk] Link extraction and prose extraction can diverge** → Keep both paths fed from the same cleaned HTML stage and test mixed cases where prose is dropped but links must remain.
- **[Risk] Heuristics may be too aggressive or too lax on some sites** → Add focused tests for known pathological inputs and tune thresholds against real corpus examples during implementation.
- **[Risk] Re-ingest changes corpus composition and search results** → Document the operational assumption clearly and verify a sample of high-value queries after rebuild.

## Migration Plan

- No schema migration is required.
- Rollout assumes the local search database can be rebuilt from source content.
- Implementation should land before the next corpus build so all chunks/links are generated with the new hygiene and chunking rules.
- If the new heuristics prove too aggressive, rollback is simply reverting the code and rebuilding the corpus from scratch.

## Open Questions

- None at the proposal stage; exact threshold constants for quality and hard safety bounds can be chosen during implementation as long as the spec-level guarantees are preserved.
