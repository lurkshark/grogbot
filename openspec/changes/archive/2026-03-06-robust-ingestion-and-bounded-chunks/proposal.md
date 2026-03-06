## Why

Bulk embedding remains vulnerable to Apple MPS out-of-memory failures because the current ingestion pipeline still admits pathological extracted content and the current chunker does not enforce a true hard upper bound on emitted chunk size. We want a corpus optimized for well-formed prose and useful outbound links, even if that means aggressively pruning noisy extracted data and re-ingesting from scratch.

## What Changes

- Add a robust ingestion hygiene pipeline for URL and feed content before chunk persistence.
- Sanitize extracted HTML aggressively to remove scripts, widgets, boilerplate, malformed content, and other low-signal artifacts before markdown/plaintext generation.
- Preserve outbound link extraction separately from prose-oriented text pruning so useful links survive even when noisy text blocks are dropped.
- Introduce hard fallback chunk splitting so every emitted chunk satisfies absolute safety bounds, even when paragraphs or sentences are unusually large or malformed.
- Add chunk-level quality filters that prefer natural-language prose and permit dropping low-signal blocks that are unlikely to help retrieval.
- Treat this as a re-ingest change: no migration or in-place rechunking path is required for existing persisted data.

## Capabilities

### New Capabilities
- `robust-content-ingestion`: Extract, sanitize, normalize, and quality-filter document content for prose-oriented indexing.
- `bounded-document-chunking`: Produce semantically useful chunks while enforcing absolute chunk-size safety bounds via fallback splitting.
- `separate-link-preservation`: Preserve outbound links from cleaned source content independently from aggressive prose cleanup.

### Modified Capabilities
- None.

## Impact

- `packages/search-core/src/grogbot_search/service.py` ingestion flow for URLs, feeds, and link extraction.
- `packages/search-core/src/grogbot_search/chunking.py` chunk splitting and chunk admission rules.
- Search corpus composition, embedding workload profile, and MPS operational reliability.
- Tests covering ingestion, chunking, link extraction, and pathological-content handling.
- README / user-facing workflow documentation describing the new ingestion and re-ingest assumptions.
