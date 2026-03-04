## 1. Link derivation updates

- [x] 1.1 Update outbound link target derivation helper(s) to accept the source document canonical URL.
- [x] 1.2 Resolve markdown href values with `urljoin(source_canonical_url, href)` before canonicalization/domain comparison.
- [x] 1.3 Skip target IDs whose normalized domain matches the source canonical domain while preserving self-link and dedupe behavior.
- [x] 1.4 Keep unknown cross-domain target handling unchanged (`to_document_id = document_id_for_url(_canonicalize_url(resolved_url))`).

## 2. Service integration

- [x] 2.1 Update `chunk_document` link insertion flow to provide source canonical URL to link-derivation logic.
- [x] 2.2 Verify no schema or API contract changes are introduced by the filtering update.

## 3. Test updates

- [x] 3.1 Update link-graph persistence tests to assert same-domain absolute links are skipped and cross-domain links persist.
- [x] 3.2 Add/adjust tests for relative-link resolution (`/path`, `../path`) being treated as same-domain and skipped.
- [x] 3.3 Update unknown-target tests to validate cross-domain unknown URLs still store derived `to_document_id`.
- [x] 3.4 Refactor link-score ranking fixtures/assertions to multi-domain documents so expected inbound-link ordering remains deterministic.

## 4. Verification

- [x] 4.1 Run `packages/search-core` tests and confirm all link graph/ranking assertions pass with same-domain filtering enabled.
- [x] 4.2 Manually sanity-check that link rows now represent cross-domain edges only for updated fixtures.
