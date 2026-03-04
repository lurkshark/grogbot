## Why

Link-based ranking currently counts links between documents on the same canonical domain. This lets intra-site link structures inflate authority and can drown out cross-site signals, reducing relevance quality.

## What Changes

- Update outbound link extraction to skip link creation when source and target resolve to the same canonical domain.
- Keep existing self-link exclusion and duplicate `(from_document_id, to_document_id)` collapse behavior.
- Resolve relative links against the source document canonical URL before domain comparison so internal relative links are also skipped.
- Apply the same-domain skip rule even when the target document has not been ingested yet (compare using canonicalized target URL).
- Update link-graph and ranking tests to use multi-domain fixtures and validate same-domain exclusion.

## Capabilities

### New Capabilities
- `document-link-domain-filtering`: Filters outbound link graph edges so only cross-domain links are persisted for ranking.

### Modified Capabilities
- *(none)*

## Impact

- Affected code: `packages/search-core/src/grogbot_search/service.py` link extraction/insertion helpers.
- Affected tests: `packages/search-core/tests/test_service.py` link-graph lifecycle tests and link-score ranking fixtures/assertions.
- API/CLI shape: no contract changes expected; link persistence and derived `link_score` values change.
- Dependencies/systems: no new dependencies; SQLite schema remains unchanged.
