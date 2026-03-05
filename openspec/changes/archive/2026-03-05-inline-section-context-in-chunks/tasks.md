## 1. Context-aware block modeling

- [x] 1.1 Update `chunking.py` parsing flow to track active heading hierarchy and associate each body block with its heading context.
- [x] 1.2 Implement heading-path normalization that emits at most the top two heading levels and supports single-level context.
- [x] 1.3 Ensure heading-only segments do not produce body blocks eligible for chunk emission.

## 2. Chunk emission and sizing behavior

- [x] 2.1 Update chunk accumulation logic to flush when context changes so one chunk does not mix body from multiple contexts.
- [x] 2.2 Prepend plain context text (`H1 > H2` with no marker) to emitted chunk text while keeping body-only word budgeting for `TARGET_WORDS` and `MAX_WORDS`.
- [x] 2.3 Preserve oversized-block sentence fallback and ensure each sentence-group chunk inherits the same context prefix.

## 3. Test coverage updates

- [x] 3.1 Extend `test_chunking.py` with golden-output tests for top-two context formatting, context-change flush behavior, and heading-only suppression.
- [x] 3.2 Add tests proving context is excluded from budget calculations and may increase total emitted words above `MAX_WORDS`.
- [x] 3.3 Update oversized-block tests to assert context preservation across sentence-split outputs.

## 4. Retrieval validation

- [x] 4.1 Add or adjust `test_service.py` assertions to verify ingested `chunks.content_text` includes inlined context for headed markdown content.
- [x] 4.2 Run targeted test suites (`test_chunking.py`, relevant `test_service.py` cases) and resolve regressions.
