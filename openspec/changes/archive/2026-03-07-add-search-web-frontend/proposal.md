## Why

Grogbot currently exposes search through the CLI and API, but it does not provide a human-facing web interface. Adding a simple web frontend now creates the first top-level system experience on `www.grogbot.com`, lets users search through a browser without going through the JSON API, and establishes the package and route pattern for future systems.

## What Changes

- Add a new Python-rendered `packages/web` package as a web frontend surface for Grogbot.
- Add a root web page at `/` that acts as the top-level domain entry point for Grogbot systems.
- Add a search landing page at `/search` with a “Grogbot Search” heading, query input, and Search button.
- Add a search results page at `/search/query?q=...` that renders the top 25 search results and includes a query input at the top for running another search.
- Make the web package use `SearchService` directly against the server-side replicated SQLite database instead of going through the API package.
- Redirect `/search/query` requests with a missing or blank `q` parameter back to `/search`.
- Allow duplicate documents in initial results when multiple chunks from the same document rank in the top 25.
- Keep the existing `packages/api` package unchanged and out of scope for this change.

## Capabilities

### New Capabilities
- `search-web`: Python-rendered web pages for Grogbot root navigation and the Search landing/results experience.

### Modified Capabilities
- None.

## Impact

- New package: `packages/web`.
- New Python web dependencies for HTML rendering and static asset serving.
- New public HTML routes at `/`, `/search`, and `/search/query`.
- New templates/static assets for the web frontend.
- No API contract changes and no `packages/api` modifications in this change.
