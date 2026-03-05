## Why

Search chunks currently rely on paragraph text alone and can emit heading-only fragments, which weakens retrieval for section-oriented queries and introduces low-value noise. We want each body chunk to carry stable section context so both FTS and vector ranking can use topical signals without changing the search schema.

## What Changes

- Inline section context into each chunk’s `content_text` as a plain prefix using the top two heading levels (for example, `API > Auth`), with no context marker.
- Exclude inline context words from chunk size budgeting; `TARGET_WORDS` and `MAX_WORDS` continue to apply to body text only.
- Stop emitting heading-only chunks and flush active chunks when section context changes to avoid mixed-topic chunks.
- Preserve oversized-block sentence fallback behavior, while carrying the same section context into each emitted sentence-group chunk.
- Add/adjust tests to lock formatting, budget rules, context transitions, and oversized split behavior.

## Capabilities

### New Capabilities
- `search-chunk-context`: Produces context-aware plaintext chunks that prepend top-level section path information to body content during ingestion.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/search-core/src/grogbot_search/chunking.py`
- Affected tests: `packages/search-core/tests/test_chunking.py` and relevant retrieval assertions in `packages/search-core/tests/test_service.py`
- Data/index impact: newly ingested documents will store context-enriched chunk text in `chunks.content_text`, which feeds both FTS and vector embedding generation
- No API shape changes expected; behavior change is in ingestion/chunk text composition
