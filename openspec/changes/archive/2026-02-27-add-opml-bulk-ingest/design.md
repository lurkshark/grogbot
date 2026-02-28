## Context

Grogbot currently supports ingestion from a single URL (`create_document_from_url`) and a single feed URL (`create_documents_from_feed`). Users with existing reader subscriptions exported as OPML must currently ingest feeds one-by-one.

This change adds an orchestration layer API that bulk ingests feeds from an OPML URL while preserving existing ingestion behavior and data model semantics. The change crosses multiple modules (search-core service, FastAPI routes, and CLI commands), so a design artifact is useful to align behavior and interfaces.

## Goals / Non-Goals

**Goals:**
- Add `create_documents_from_opml(opml_url)` to `SearchService`.
- Parse OPML outlines recursively and collect all `xmlUrl` feed URLs, including nested outlines.
- Use best-effort processing: failures on one feed do not prevent processing remaining feeds.
- Keep return parity with feed ingestion by returning a flat `List[Document]`.
- Expose OPML ingest consistently in API and CLI.

**Non-Goals:**
- Changing how individual feed ingestion works inside `create_documents_from_feed`.
- Introducing a new orchestration result type (e.g., per-feed success/error report).
- Adding asynchronous/background ingestion infrastructure.

## Decisions

### 1) Orchestration location: `SearchService`
`create_documents_from_opml` will live in `SearchService`, next to other ingestion methods.

- **Why:** Keeps ingestion orchestration in one domain/service layer and lets API/CLI remain thin wrappers.
- **Alternative considered:** Implement OPML logic separately in API/CLI. Rejected due to duplicated logic and inconsistent behavior.

### 2) OPML parsing strategy: XML tree traversal, recursive/nested extraction
OPML content will be fetched from the URL and parsed as XML. The implementation will traverse nested `<outline>` nodes and collect `xmlUrl` values.

- **Why:** OPML feed lists are XML with nested outlines, and `xmlUrl` is the standard feed location attribute.
- **Alternative considered:** Flat parsing only top-level outlines. Rejected because nested folders/categories are common in exported OPML.

### 3) Execution model: best-effort per feed
For each extracted feed URL, call `create_documents_from_feed` in a `try/except` boundary and continue on failure.

- **Why:** Matches user expectation for bulk import robustness and prevents one broken feed from failing the entire job.
- **Alternative considered:** Fail-fast behavior. Rejected based on explicit product decision.

### 4) Return contract: parity with feed ingestion
`create_documents_from_opml` returns a flat `List[Document]` containing documents created/updated from all successfully ingested feeds.

- **Why:** Preserves consistency with existing `create_documents_from_feed` return type and avoids broad API contract changes.
- **Alternative considered:** Return a structured report (`documents`, `errors`, `feeds_processed`). Rejected for this iteration to preserve parity.

### 5) Surface consistency: API + CLI wrappers
Add:
- API: `POST /search/ingest/opml` with `{ opml_url: string }`
- CLI: `grogbot search ingest-opml <opml_url>`

- **Why:** Existing ingestion operations are available through both surfaces; OPML ingestion should follow the same product pattern.

## Risks / Trade-offs

- **Silent partial failures (best-effort + parity return)** → Document list alone does not identify failed feeds. Mitigation: keep behavior intentional and consider logging/telemetry in implementation.
- **Malformed or non-OPML XML inputs** → Parsing may fail early. Mitigation: treat parse/fetch errors as operation failure for OPML URL, but continue per-feed once URLs are extracted.
- **Duplicate feed URLs in OPML** → Potential duplicate ingest attempts. Mitigation: normalize/trim and deduplicate feed URLs before processing.
- **Large OPML files** → Longer ingestion times and many downstream feed requests. Mitigation: retain sequential flow for now; revisit batching/async later if needed.

## Migration Plan

- No schema/database migration required.
- Backward compatible additions only:
  - new service method,
  - new API route,
  - new CLI command.
- Rollback path: remove OPML-specific route/command/method without affecting existing URL/feed ingestion.

## Open Questions

- Should we emit per-feed failure logs by default (and if so, where) while keeping return parity?
- Should feed URL normalization include canonical URL parsing beyond trim/dedupe in this iteration?
