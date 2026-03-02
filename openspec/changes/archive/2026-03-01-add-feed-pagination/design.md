## Context

Search ingestion currently parses a single RSS/Atom feed URL via `SearchService.create_documents_from_feed`, which uses `feedparser` and does not follow pagination. Some feeds expose additional pages through `<link rel="next">` so ingesting only the first page misses older entries. The API, CLI, and bootstrap flows call this method directly.

## Goals / Non-Goals

**Goals:**
- Add an optional pagination mode to feed ingestion that follows `<link rel="next">` links up to 100 pages.
- Keep default behavior unchanged (`paginate=False`).
- Propagate `paginate` through OPML ingestion, API, CLI, and CLI bootstrap.
- Best-effort pagination: failures on later pages stop pagination while preserving already-ingested documents.

**Non-Goals:**
- Changing feed parsing logic beyond pagination.
- Adding logging/telemetry for pagination stops.
- Expanding pagination support to sitemaps or URL ingestion.

## Decisions

1. **Pagination discovery via `feedparser` links**
   - Use `feed.feed.get("links")` and select the first entry with `rel == "next"`.
   - Rationale: `feedparser` already normalizes feed-level links; this keeps parsing consistent with existing feed ingestion.
   - Alternatives: parse XML directly or use HTTP Link headers. Rejected due to complexity and inconsistent availability.

2. **URL resolution and loop protection**
   - Resolve relative `href` values via `urljoin(current_feed_url, href)`.
   - Maintain a `seen_feed_urls` set to prevent cycles and duplicate requests.
   - Rationale: some feeds provide relative links and occasional looping pagination.

3. **Pagination limits and best-effort behavior**
   - Enforce a hard cap of 100 pages.
   - On any exception while fetching/parsing subsequent pages, stop pagination and return accumulated documents.
   - Rationale: prevents runaway pagination and ensures partial success is preserved.

4. **API/CLI surface changes**
   - Add `paginate: bool = False` to the ingest feed request model and CLI command option.
   - Update CLI bootstrap to call feed ingestion with `paginate=True`.
   - Rationale: keeps backwards compatibility while enabling opt-in pagination where needed.

## Risks / Trade-offs

- **Increased network usage when enabled** → Mitigated by opt-in flag and 100-page cap.
- **Feeds with malformed `rel=next` links** → Mitigated by `seen` tracking and best-effort stop on errors.
- **Longer ingest times for large feeds** → Mitigated by default `paginate=False`.

## Migration Plan

- No data migrations required.
- Deploy code changes; existing callers remain compatible because `paginate` defaults to `False`.

## Open Questions

- None.
