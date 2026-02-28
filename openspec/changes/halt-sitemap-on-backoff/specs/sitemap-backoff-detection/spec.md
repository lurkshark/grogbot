## ADDED Requirements

### Requirement: Sitemap ingestion MUST classify backoff responses
The sitemap ingestion flow MUST classify a URL fetch as a backoff condition when any of the following signals are present: HTTP status `401`, `403`, `429`, or `503`; a `Retry-After` response header; or CAPTCHA/challenge page indicators in the response body.

#### Scenario: Status code indicates backoff
- **WHEN** sitemap ingestion fetches a page URL and receives HTTP `403`
- **THEN** the response is classified as a backoff condition

#### Scenario: Retry-After header indicates backoff
- **WHEN** sitemap ingestion fetches a page URL and receives a response containing `Retry-After`
- **THEN** the response is classified as a backoff condition even if status is not one of `401/403/429/503`

#### Scenario: CAPTCHA body indicates backoff
- **WHEN** sitemap ingestion fetches a page URL and receives HTTP `200` with CAPTCHA/challenge indicators in the body
- **THEN** the response is classified as a backoff condition

### Requirement: Sitemap ingestion MUST halt immediately on backoff
When a backoff condition is detected for any URL in a sitemap run, the system MUST stop processing additional sitemap URLs and MUST raise an error to the caller.

#### Scenario: Backoff halts remaining URLs
- **WHEN** a sitemap contains URLs `A`, `B`, and `C`, and URL `B` produces a backoff condition
- **THEN** ingestion raises an error and URL `C` is not fetched

#### Scenario: Caller observes explicit failure
- **WHEN** sitemap ingestion encounters a backoff condition
- **THEN** CLI/API callers receive an error instead of a silent partial-success response

### Requirement: Non-backoff failures MUST remain best-effort
The sitemap ingestion flow MUST continue processing remaining URLs when a URL fails for a non-backoff reason (for example `404` or parsing failure).

#### Scenario: Non-backoff HTTP error is skipped
- **WHEN** a sitemap URL returns `404` without any backoff signal
- **THEN** that URL is skipped and later sitemap URLs are still processed
