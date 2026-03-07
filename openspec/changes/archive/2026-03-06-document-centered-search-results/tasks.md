## 1. Search query semantics

- [x] 1.1 Update `SearchService.search()` to collapse hybrid-scored chunk candidates to one representative chunk per document using SQL windowing.
- [x] 1.2 Apply the final result limit after document deduplication so `limit` counts unique documents.
- [x] 1.3 Preserve deterministic ordering and representative-chunk selection when scores tie.

## 2. Result assembly and interface compatibility

- [x] 2.1 Keep the existing `SearchResult` shape while ensuring each result represents a unique document and its selected chunk.
- [x] 2.2 Verify CLI and API search behavior remains schema-compatible with the new document-centered semantics.

## 3. Test coverage

- [x] 3.1 Update search tests to cover unique-document results when multiple chunks from one document match.
- [x] 3.2 Add tests for document-based limit behavior and representative-chunk selection.
- [x] 3.3 Validate edge cases such as deterministic ties and missing chunk rows after scoring.
