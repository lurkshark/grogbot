## 1. Search service refactor

- [x] 1.1 Update `SearchService.upsert_document` to reject empty/whitespace-only content, delete chunks only on content change, and never create chunks
- [x] 1.2 Add `SearchService.chunk_document(document_id)` to load the document, clear chunks, recreate chunks via `_create_chunks`, and return the created chunk count (raise not-found for missing ids)
- [x] 1.3 Add `SearchService.synchronize_document_chunks(maximum=None)` to find chunkless documents ordered by id, apply the optional maximum, chunk each document, and return total chunks created

## 2. API and CLI exposure

- [x] 2.1 Add API endpoints/models for single-document chunking (404 on missing document) and bulk chunking with optional maximum, returning created chunk counts
- [x] 2.2 Add CLI commands to invoke single-document and bulk chunking, including a maximum option for bulk

## 3. Ingestion updates

- [x] 3.1 Ensure ingestion helpers skip empty content before calling `upsert_document`
- [x] 3.2 Update ingestion flows to explicitly call chunking after upserts where needed

## 4. Test updates

- [x] 4.1 Update search/ingestion tests to call chunking during setup before assertions
- [x] 4.2 Add tests for chunking APIs/CLI commands and for rejecting empty document content
