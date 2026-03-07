## Context

Grogbot currently has a search core library plus CLI and API packages, but no browser-facing frontend. The desired first web experience is intentionally small: a root page for the domain, a Search landing page at `/search`, and a Search results page at `/search/query?q=...`.

The repository is currently Python-based and already uses FastAPI/ASGI patterns. The new web package should fit that ecosystem, render HTML on the server, and read from the server-side replicated SQLite database through `SearchService`. This change explicitly avoids changing the existing `packages/api` package so that the first frontend slice stays focused on human-facing pages instead of JSON API redesign.

## Goals / Non-Goals

**Goals:**
- Add a new `packages/web` package that provides a Python-rendered frontend.
- Provide domain-level HTML routes for `/`, `/search`, and `/search/query`.
- Render the initial search experience on the server, including the first page of results.
- Reuse `SearchService` directly so web and other surfaces share the same search behavior and database configuration.
- Keep the implementation small and easy to evolve into additional top-level systems later.

**Non-Goals:**
- Changing or removing any routes from `packages/api`.
- Introducing a JavaScript-heavy SPA architecture.
- Redesigning search ranking or converting chunk results into document-deduplicated results.
- Defining a final unified public deployment topology for web and API on the same host.

## Decisions

### 1. Build `packages/web` as a Python-rendered ASGI package
- Decision: The frontend will be a Python package in the uv workspace, using server-rendered templates and static asset serving.
- Why: This matches the current Python-only repository, avoids introducing a second toolchain, and is sufficient for the initial search experience.
- Alternative considered: adding a JS/TS frontend package; rejected for now because the first scope is simple and does not justify extra build and deployment complexity.

### 2. Call `SearchService` directly from web routes
- Decision: The web package will resolve configuration the same way as CLI/API and will execute searches through `SearchService` directly.
- Why: This avoids internal HTTP calls, reduces latency and coupling, and keeps the API package out of scope.
- Alternative considered: rendering pages by calling the existing API over HTTP; rejected because it adds unnecessary indirection and would couple page rendering to API route design.

### 3. Use top-level human-facing routes
- Decision: The web package will own `/`, `/search`, and `/search/query`.
- Why: These routes match the intended product shape where each Grogbot system lives at a top-level path segment and Search owns its main interface directly under `/search`.
- Alternative considered: nesting Search UI deeper under another prefix; rejected because it weakens the intended domain structure.

### 4. Server-render `/search/query` from the query string
- Decision: `GET /search/query?q=...` will render HTML with results already present in the response.
- Why: This keeps the first version simple, makes URLs shareable, works without JavaScript, and aligns with the familiar search-engine interaction model.
- Alternative considered: serving an app shell that fetches results client-side after load; rejected because it adds complexity without clear benefit for v1.

### 5. Redirect empty queries back to `/search`
- Decision: Requests to `/search/query` with a missing or blank `q` parameter will redirect to `/search` rather than rendering an empty results page.
- Why: The landing page is the canonical empty-search experience, and redirecting keeps the route semantics clean.
- Alternative considered: rendering a no-results or empty-state page at `/search/query`; rejected because it duplicates the landing-page role.

### 6. Preserve current chunk-level result behavior in the web UI
- Decision: The results page will display the top 25 results returned by `SearchService.search(..., limit=25)` in service order, even when that means duplicate documents appear.
- Why: This keeps the frontend aligned with current engine behavior and avoids introducing document-grouping semantics in the first web change.
- Alternative considered: deduplicating or regrouping results by document in the web layer; rejected for now because it changes presentation semantics and raises ranking questions outside this change.

### 7. Keep deployment coupling loose
- Decision: The design defines the web package and its route behavior, but does not require a specific merged deployment with the existing API package.
- Why: The current package scope is intentionally limited to web. Deployment composition can be decided later without blocking implementation of the frontend itself.
- Alternative considered: coupling this design to an `/api/*` migration or combined host strategy; rejected because that would expand scope into API redesign.

## Risks / Trade-offs

- **[Risk] Route collisions with the existing API if both are later exposed on the same host/path space** → **Mitigation:** treat deployment composition as a later decision and keep API changes out of this change.
- **[Risk] Duplicate documents in results may feel less polished than mainstream search engines** → **Mitigation:** accept this as an explicit v1 trade-off and revisit grouped results in a later change if needed.
- **[Risk] Server-rendered templates may need refactoring if the frontend becomes highly interactive later** → **Mitigation:** keep presentation concerns isolated in `packages/web` so richer client-side behavior can be added incrementally.
- **[Risk] Web requests depend directly on database availability and search-service performance** → **Mitigation:** reuse existing service/config patterns and keep the initial page design lightweight.

## Migration Plan

1. Add `packages/web` to the workspace and create its ASGI entrypoint, templates, and static assets.
2. Implement root and search routes using existing config resolution and `SearchService` access.
3. Deploy the new web package in the chosen environment without changing `packages/api` behavior.
4. If rollback is needed, undeploy or disable the web package; no data migration is required because this change only adds a read-only presentation layer.

## Open Questions

- No blocking product questions remain for this first slice. Public coexistence with the existing API can be decided in a later change if both need to share a single hostname.
