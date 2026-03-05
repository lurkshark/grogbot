## Why

`RuntimeError: MPS backend out of memory` is occurring during bulk embedding synchronization even when embedding batch size is reduced. The current chunking bounds (`TARGET_WORDS=1536`, `MAX_WORDS=5324`) permit very large chunks that can still create high per-encode memory spikes on Apple MPS.

Separately, search-core still exposes backward-compatible alias methods (`chunk_document`, `synchronize_document_chunks`) that duplicate the newer embedding method names and keep legacy API surface area alive.

## What Changes

- Reduce chunk size limits in `chunking.py` to:
  - `TARGET_WORDS = 512`
  - `MAX_WORDS = 1024`
- Keep chunking behavior the same otherwise (section/paragraph/sentence splitting logic unchanged).
- **BREAKING** Remove backward-compatible alias methods from `SearchService`:
  - remove `chunk_document` alias (use `embed_document_chunks`)
  - remove `synchronize_document_chunks` alias (use `synchronize_document_embeddings`)
- Update internal call sites/tests/docs that still reference alias names.

## Capabilities

### Modified Capabilities
- `document-chunking`: tune target/max chunk word bounds to lower embedding-time memory risk on MPS.
- `chunk-embedding-sync`: normalize service API to canonical embedding method names only, dropping legacy aliases.

### New Capabilities
- None.

## Impact

- `packages/search-core/src/grogbot_search/chunking.py` (new chunk size constants).
- `packages/search-core/src/grogbot_search/service.py` (alias removal).
- Tests and any callers currently using `chunk_document` / `synchronize_document_chunks` must migrate.
- User assumption for rollout: database starts empty and corpus is fully re-ingested, so no rechunk migration path is required in this change.
