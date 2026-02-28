## Why

Sitemap ingestion currently treats all per-URL failures as best-effort and continues scraping. When a target site starts returning anti-bot/backoff responses (for example CAPTCHA, 401/403, or rate-limit signals), continuing requests is counterproductive and can worsen blocking.

## What Changes

- Update sitemap ingestion behavior to detect explicit backoff signals while fetching sitemap page URLs.
- Immediately halt sitemap scraping by raising an error when a backoff signal is detected.
- Keep existing best-effort behavior for non-backoff failures (for example 404 or parse failures) so ingestion can still proceed through ordinary bad URLs.
- Add/adjust tests to verify halt-on-backoff behavior and continued skip-on-non-backoff behavior.

## Capabilities

### New Capabilities
- `sitemap-backoff-detection`: Detects backoff/challenge responses during sitemap URL ingestion and stops further scraping immediately.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/search-core/src/grogbot_search/service.py` (`create_documents_from_sitemap` and helper logic).
- Affected tests: sitemap ingestion tests in `packages/search-core/tests/test_ingestion.py` and HTTP fixture behavior in `packages/search-core/tests/conftest.py`.
- API/CLI impact: `/search/ingest/sitemap`, `grogbot search ingest-sitemap`, and `grogbot search bootstrap` may now fail fast when backoff is encountered instead of silently returning partial results.
