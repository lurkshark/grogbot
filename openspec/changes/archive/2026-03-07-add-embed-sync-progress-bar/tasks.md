## 1. Search core progress reporting

- [x] 1.1 Add a raw progress snapshot type for bulk embedding synchronization in `packages/search-core/src/grogbot_search/` and export it if needed by callers
- [x] 1.2 Extend `SearchService.synchronize_document_embeddings(maximum=...)` to accept an optional per-document progress callback without changing its integer return value
- [x] 1.3 Emit an initial progress snapshot for the selected document set and one updated snapshot after each completed document, including cumulative vectors created
- [x] 1.4 Add or update `packages/search-core/tests/test_service.py` coverage for callback invocation order, reported totals, and `maximum`-scoped progress totals

## 2. CLI progress experience

- [x] 2.1 Update `packages/cli/src/grogbot_cli/app.py` so `grogbot search document embed-sync` wires a callback into `synchronize_document_embeddings`
- [x] 2.2 Render a live progress bar with completed documents, total selected documents, elapsed time, and ETA in the CLI package while synchronization runs
- [x] 2.3 Keep live progress output separate from the final stdout JSON result and add any explicit CLI dependency declaration required for the chosen progress renderer

## 3. Validation and documentation

- [x] 3.1 Add CLI-facing tests or other verification covering progress initialization and preservation of the final machine-readable output
- [x] 3.2 Update README or CLI documentation to describe live progress behavior for `grogbot search document embed-sync`
