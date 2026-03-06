## 1. Shared ingestion hygiene

- [x] 1.1 Add a shared content-cleanup pipeline in `packages/search-core/src/grogbot_search/service.py` that both URL ingestion and feed ingestion use before chunk text generation.
- [x] 1.2 Sanitize extracted HTML/content to remove non-content elements, unsafe links, comments, and obvious widget/script/style artifacts before markdown/plaintext derivation.
- [x] 1.3 Normalize extracted text (Unicode, whitespace, control/zero-width junk) and reject documents that have no usable prose after cleanup.
- [x] 1.4 Add block-level quality filtering so clearly low-signal content can be dropped before chunk generation.

## 2. Separate link preservation from prose pruning

- [x] 2.1 Refactor link extraction to run from cleaned source content rather than only from already-pruned markdown chunk text.
- [x] 2.2 Preserve existing canonicalization, relative-link resolution, and eligibility filtering while ensuring valid outbound links survive aggressive prose cleanup.
- [x] 2.3 Update ingestion flow so chunk text generation and link persistence consume the same cleaned source stage but can diverge on prose-pruning outcomes.

## 3. Hard-bounded chunk generation

- [x] 3.1 Extend `packages/search-core/src/grogbot_search/chunking.py` to keep semantic-first chunking for ordinary prose while enforcing absolute limits on every emitted chunk.
- [x] 3.2 Add progressive fallback splitting for oversized content (sentence → simpler internal boundaries → fixed windows / final hard fallback).
- [x] 3.3 Introduce a secondary non-word safety bound and ensure final chunk admission checks apply to emitted chunk text including context prefixes.
- [x] 3.4 Allow persistently low-signal pathological content to be dropped instead of persisted as chunks.

## 4. Verification and documentation

- [x] 4.1 Add/adjust tests for URL ingestion, feed ingestion, cleanup normalization, empty-after-cleanup rejection, and low-signal content dropping.
- [x] 4.2 Add/adjust tests for link preservation when prose is dropped, plus unsafe-link and relative-link handling through the cleaned-content path.
- [x] 4.3 Add/adjust chunking tests covering oversized single-sentence blocks, punctuation-poor blobs, hard safety bounds, and dropped pathological blocks.
- [x] 4.4 Update README or operator docs to explain the robustness-oriented ingestion behavior and the expectation of rebuilding the corpus with re-ingestion.
