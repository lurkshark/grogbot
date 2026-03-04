## 1. Schema and model updates

- [ ] 1.1 Add `links` table creation to `SearchService._init_schema` with `(from_document_id, to_document_id)` primary key and FK cascade on `from_document_id`
- [ ] 1.2 Add an index on `links.to_document_id` for inbound count lookups
- [ ] 1.3 Extend `SearchResult` in `packages/search-core/src/grogbot_search/models.py` with required `link_score: float`

## 2. Link extraction and lifecycle behavior

- [ ] 2.1 Implement markdown outbound-link extraction helper(s) in `service.py` and normalize each href with `_canonicalize_url`
- [ ] 2.2 Derive `to_document_id` via `document_id_for_url` for every extracted target and dedupe pairs per source document
- [ ] 2.3 Update `upsert_document` to delete outbound links for a document when `content_markdown` changes
- [ ] 2.4 Update `chunk_document` to clear existing outbound links for the source document, ignore self-links, and insert refreshed links alongside chunk regeneration

## 3. Search rank fusion integration

- [ ] 3.1 Extend the `search` SQL CTE pipeline to compute candidate-document inbound-link counts from `links`
- [ ] 3.2 Add reciprocal `link_score` ranking (`1.0 / (1 + row_number)`) ordered by inbound count DESC then document id ASC
- [ ] 3.3 Ensure documents with zero inbound links receive `link_score = 0.0` via `COALESCE`
- [ ] 3.4 Update final score computation to `fts_score + vector_score + link_score` and map `link_score` into returned `SearchResult` objects

## 4. Test coverage

- [ ] 4.1 Add tests verifying unique `(from,to)` storage and collapse of multiple same-target links within one source document
- [ ] 4.2 Add tests verifying unknown target URLs are stored via `document_id_for_url(_canonicalize_url(url))`
- [ ] 4.3 Add tests verifying self-links are ignored and outbound links are cleared on content change/document delete/chunk refresh
- [ ] 4.4 Add ranking tests verifying three-signal additive scoring, deterministic tie handling, and `link_score = 0.0` for zero-inbound documents
- [ ] 4.5 Add result-shape tests verifying `link_score` is present in query results (service/API/CLI JSON output paths as applicable)

## 5. Validation and readiness

- [ ] 5.1 Run `uv run pytest packages/search-core/tests` and confirm passing coverage for updated behavior
- [ ] 5.2 Update any remaining user/developer-facing wording that describes search scoring to include the new `link_score` signal