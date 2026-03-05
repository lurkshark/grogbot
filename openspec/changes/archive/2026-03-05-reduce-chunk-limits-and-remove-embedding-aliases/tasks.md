## 1. Update chunk-size configuration

- [x] 1.1 Change `TARGET_WORDS` to `512` in `packages/search-core/src/grogbot_search/chunking.py`.
- [x] 1.2 Change `MAX_WORDS` to `1024` in `packages/search-core/src/grogbot_search/chunking.py`.
- [x] 1.3 Update/add tests that assert chunking behavior under the new bounds.

## 2. Remove embedding alias methods

- [x] 2.1 Remove `SearchService.chunk_document` alias.
- [x] 2.2 Remove `SearchService.synchronize_document_chunks` alias.
- [x] 2.3 Update all call sites and tests to use `embed_document_chunks` and `synchronize_document_embeddings`.

## 3. Validate and document behavior

- [x] 3.1 Update user/developer docs mentioning removed alias names.
- [x] 3.2 Run search-core tests and confirm no alias references remain.
- [x] 3.3 Confirm CLI/API embedding behavior is unchanged externally (`vectors_created` responses).
