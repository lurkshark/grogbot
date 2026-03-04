## Why

Search currently ranks chunks using only FTS and vector signals, so it misses an important authority cue: documents that are frequently linked by other documents should generally rank higher. Adding a link-based rank signal now improves relevance using data we already ingest in document content.

## What Changes

- Add persistent document-to-document link storage using `from_document_id` and `to_document_id` pairs, with uniqueness per pair (no intra-document duplicate counts).
- Generate and refresh outbound links for a document during `chunk_document(document_id)` by parsing links from the document content.
- Remove outbound links from a document whenever its content changes or the document is deleted, matching chunk lifecycle semantics.
- Store links to not-yet-ingested targets by canonicalizing target URLs and deriving `to_document_id` via `document_id_for_url`.
- Extend search rank fusion with a third, equal-weight signal (`link_score`) based on inbound-link rank (in-degree), where documents with zero inbound links receive `link_score = 0.0`.
- Expose `link_score` in search results alongside `fts_score`, `vector_score`, and total `score`.

## Capabilities

### New Capabilities
- `document-link-graph`: Manage outbound document links derived from document content and kept in sync with document chunking/deletion lifecycle.
- `search-link-rank-fusion`: Add a link-based reciprocal-rank signal to search scoring and expose per-result link scoring metadata.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/search-core/src/grogbot_search/service.py`, `packages/search-core/src/grogbot_search/models.py`, `packages/search-core/src/grogbot_search/__init__.py`.
- Affected tests: `packages/search-core/tests/test_service.py` (link persistence/lifecycle, scoring, and result payload assertions).
- API/CLI contracts: search response payload includes new `link_score` field; query endpoints/commands remain unchanged.
- Database/schema: new `links` table and related indexes/constraints/triggers as needed.