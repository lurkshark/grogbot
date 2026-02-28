## Context

`create_documents_from_sitemap` currently processes sitemap URLs in a best-effort loop. Any exception from `create_document_from_url` is swallowed and ingestion continues. This works for ordinary bad URLs (for example 404 pages) but is harmful when the target starts signaling anti-bot pressure (CAPTCHA/challenge pages, authorization blocks, or rate limiting).

The requested behavior is to stop scraping immediately on backoff signals while preserving best-effort skipping for non-backoff failures.

## Goals / Non-Goals

**Goals:**
- Detect backoff/challenge signals during sitemap URL ingestion.
- Fail fast by raising an error as soon as a backoff signal is observed.
- Preserve existing best-effort handling for non-backoff failures.
- Make behavior deterministic and testable for status code, headers, and body-based challenge detection.

**Non-Goals:**
- Adding retry logic, adaptive throttling, or circuit breaking.
- Changing feed or OPML ingestion behavior.
- Guaranteeing transactional rollback of documents already ingested before backoff is detected.

## Decisions

1. **Introduce explicit backoff classification for sitemap URL fetches.**
   - Backoff signals include: HTTP `401`, `403`, `429`, `503`, presence of `Retry-After` header, and CAPTCHA/challenge indicators in response body.
   - Rationale: this captures both explicit status-based blocks and common anti-bot soft blocks where status is `200`.
   - Alternative considered: status-code-only detection. Rejected because CAPTCHA pages often return `200`.

2. **Raise a dedicated ingestion error when backoff is detected.**
   - `create_documents_from_sitemap` will raise a specific exception type (or an equivalently distinct error signal) on backoff so callers can differentiate from routine per-URL failures.
   - Rationale: preserves clear control flow and supports API/CLI fail-fast semantics.
   - Alternative considered: silently returning partial documents on backoff. Rejected because it hides meaningful operational signals.

3. **Keep best-effort continuation for non-backoff per-URL failures.**
   - Non-backoff exceptions (network issues, parse failures, 404s) continue to be skipped as today.
   - Rationale: avoids regressions in resilience to imperfect sitemaps while enforcing safer behavior under block pressure.

4. **Treat behavior as halt-forward, not all-or-nothing.**
   - Documents ingested before backoff detection remain persisted.
   - Rationale: aligns with current per-document upsert model and avoids introducing transaction-wide complexity in this change.

## Risks / Trade-offs

- **[False-positive challenge detection]** Broad body keyword matching could classify benign pages as CAPTCHA/backoff → **Mitigation:** start with conservative markers (e.g., `captcha`, `cf-chl`, `attention required`) and adjust via tests.
- **[Behavioral change for callers]** CLI/API/bootstrap flows may now fail where they previously returned partial results → **Mitigation:** clear exception messages and explicit tests for fail-fast behavior.
- **[Partial ingestion before halt]** Some documents may be stored before a later URL triggers backoff → **Mitigation:** document halt-forward semantics and leave transactional ingestion as future enhancement.

## Migration Plan

- No data migration required.
- Rollout is code + tests only.
- Rollback strategy: revert to prior sitemap loop behavior that swallows all per-URL exceptions.

## Open Questions

- Should backoff classification be reused by feed/OPML or URL ingestion in a future follow-up?
- Should challenge pattern matching be configurable per source/domain later?
