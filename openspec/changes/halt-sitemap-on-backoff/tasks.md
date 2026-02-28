## 1. Backoff detection primitives

- [ ] 1.1 Add a sitemap-ingestion backoff classification helper that detects status-based (`401/403/429/503`), header-based (`Retry-After`), and CAPTCHA/challenge body signals.
- [ ] 1.2 Add a dedicated exception (or equivalent explicit error signal) for backoff detection so callers can distinguish it from ordinary per-URL failures.

## 2. Sitemap ingestion fail-fast behavior

- [ ] 2.1 Update `create_documents_from_sitemap` to raise immediately when a URL fetch is classified as backoff.
- [ ] 2.2 Preserve current best-effort continuation for non-backoff URL failures during sitemap ingestion.
- [ ] 2.3 Ensure halt-forward semantics are retained (documents ingested before the backoff event remain persisted).

## 3. Verification and regression tests

- [ ] 3.1 Extend test HTTP fixtures to simulate backoff responses (403/429/503, Retry-After header, CAPTCHA-like body).
- [ ] 3.2 Add ingestion tests proving sitemap processing halts on backoff and does not fetch subsequent URLs.
- [ ] 3.3 Add/adjust tests proving non-backoff failures (for example 404) are still skipped best-effort.
- [ ] 3.4 Add API/CLI integration tests to confirm ingest sitemap surfaces failure when backoff occurs.
