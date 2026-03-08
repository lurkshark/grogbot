## Context

The current web app already serves three HTML experiences from the `app` package: a root page at `/`, a search landing page at `/search`, and a search results page at `/search/query`. Functionally the routes are simple and sufficient, but the presentation is intentionally roomy: the root and search landing pages use hero-style layouts, the search controls are pill-shaped, and result snippets render full chunk text.

That presentation works on desktop, but it wastes vertical space on phones and makes the app feel more like a marketing landing page than a compact search tool. The requested direction is to keep the existing routes and ranked result behavior while redesigning the UI around a thin persistent Grogbot stripe, near-titleless search pages, tighter rectangular controls, and short query-aware snippets with optional literal-term highlighting.

Constraints:
- This change should stay inside the `packages/app` web layer and not alter search-core ranking, chunk persistence, or result ordering semantics.
- Duplicate document results remain allowed if returned by the search service.
- Snippet shortening is a presentation concern, so stored chunk text should remain unchanged.
- Highlighting must remain safe in server-rendered HTML and must not introduce unescaped user-controlled markup.

## Goals / Non-Goals

**Goals:**
- Make `/`, `/search`, and `/search/query` feel compact and mobile-first.
- Introduce a shared thin Grogbot brand stripe across all app pages.
- Replace the current pill-shaped search controls with lightly rounded rectangular controls.
- Reduce result density by rendering snippets at roughly 120 visible characters.
- Prefer snippets that begin near meaningful literal query-term matches and visually highlight those visible matches when present.
- Preserve the current route structure, search request flow, and ranked result ordering.

**Non-Goals:**
- Changing search-core scoring, deduplication, or chunk selection behavior.
- Rewriting stored chunk text or adding new database fields for snippets.
- Introducing client-side JavaScript search rendering.
- Building semantic snippet selection beyond literal query-term matching.
- Precisely specifying pixel-perfect visual design in the spec layer.

## Decisions

### 1. Add shared chrome in the base template
- **Decision:** Move Grogbot branding into a shared top stripe rendered from the base layout so all pages inherit the same thin header.
- **Rationale:** The brand stripe is a cross-page requirement. Implementing it once in shared chrome keeps the root, landing, and results pages visually consistent and avoids duplicating markup.
- **Alternative considered:** Repeating page-local branding blocks in each template. Rejected because the stripe is intentionally global and duplicated markup would drift.

### 2. Convert root and search pages from hero layouts to compact utility layouts
- **Decision:** Remove the dominant hero posture from `/` and `/search`. Keep `/` as a compact entry page for the app and make `/search` nearly titleless with the search form near the top of the content area.
- **Rationale:** This delivers the requested mobile-first compactness without changing route responsibilities. `/` stays a top-level entry point, but no page should consume large vertical space before the primary action is visible.
- **Alternative considered:** Keeping the existing hero layouts and only tightening spacing. Rejected because the hero structure itself is the main source of wasted vertical space.

### 3. Shift control styling from pill-shaped to lightly rounded rectangles
- **Decision:** Update shared CSS so search inputs and buttons use modest corner radii, tighter padding, and compact spacing.
- **Rationale:** The current fully rounded controls visually emphasize softness and spaciousness. Mildly rectangular controls better match the desired dense search-tool aesthetic while remaining touch-friendly on mobile.
- **Alternative considered:** Hard square corners. Rejected because they would look harsher than requested and reduce visual softness unnecessarily.

### 4. Generate display snippets in the app layer, not the search layer
- **Decision:** Add an app-layer snippet formatting helper that accepts the raw chunk text and query string, returns a display snippet of about 120 visible characters, and leaves search-core models unchanged.
- **Rationale:** The stored chunk remains the authoritative retrieval text. Formatting for HTML presentation belongs in the web layer and should not change API or CLI payloads.
- **Alternative considered:** Truncating or re-centering snippets in search-core results. Rejected because it would leak a web-specific presentation concern into shared search behavior.

### 5. Use keyword-forward windowing with trailing ellipsis only
- **Decision:** When a meaningful literal query-term match exists, start the snippet slightly before the first strong visible match instead of perfectly centering it, then truncate to roughly 120 visible characters and append only a trailing ellipsis when trimming occurs.
- **Rationale:** True centering often requires both leading and trailing ellipses. The requested behavior explicitly prefers only a trailing ellipsis, so the snippet should feel like a natural excerpt that begins near the match rather than a mid-stream slice.
- **Alternative considered:** Perfectly centered windows with leading and trailing ellipses. Rejected because it conflicts with the requested snippet style.

### 6. Highlight only literal query-term matches visible in the rendered snippet
- **Decision:** Highlight matched terms in the visible snippet using safe server-rendered markup, but only for literal case-insensitive query-term matches that actually appear in the displayed excerpt.
- **Rationale:** This gives users useful search feedback while keeping the feature explainable and honest. Vector-only relevance may produce useful results without literal terms, and those snippets should remain unhighlighted rather than pretending to know semantic spans.
- **Alternative considered:** No highlighting or semantic highlighting. No highlighting misses a requested affordance; semantic highlighting is ambiguous and much harder to justify or test.

### 7. Keep result ordering and duplicate-result behavior unchanged
- **Decision:** The results page will still render results in the order returned by `SearchService.search()` and will not deduplicate documents in the app layer.
- **Rationale:** This preserves current search semantics and keeps the change focused on presentation.
- **Alternative considered:** Using the compact redesign as an opportunity to collapse duplicate documents. Rejected because it changes behavior outside the scope of the requested design work.

## Risks / Trade-offs

- **[Risk] Approximate 120-character snippets may cut sentence flow awkwardly** → **Mitigation:** trim on word boundaries where practical and use a clean leading excerpt fallback when no useful match is present.
- **[Risk] Query token matching can over-highlight common words or punctuation fragments** → **Mitigation:** ignore blank tokens and very short low-signal terms during snippet matching/highlighting.
- **[Risk] Safe highlighting in server-rendered HTML can accidentally double-escape or under-escape content** → **Mitigation:** escape raw text first, then apply highlighting only to escaped display fragments or otherwise use a safe templating pathway with explicit tests.
- **[Trade-off] Root and search pages become visually more similar** → **Accepted:** the compact search-tool posture is more important than maintaining a large visual distinction between pages.
- **[Trade-off] Snippet selection remains literal-term-aware, not semantic** → **Accepted:** this is simpler, predictable, and sufficient for the requested UI improvement.

## Migration Plan

1. Update shared template chrome and CSS so all pages render under the new brand stripe.
2. Refactor root and search landing templates to use the compact layout.
3. Add app-layer snippet formatting/highlighting helpers and switch results rendering to those derived values.
4. Update app tests to cover shared branding chrome, compact page expectations, snippet truncation, and visible highlighting.
5. Rollback, if needed, is straightforward: restore the previous templates/CSS and render raw chunk text again because no persistent data model changes are involved.

## Open Questions

- Whether `/` should eventually become a full search entry point instead of a compact launcher remains a future product choice, but this design keeps the existing route purpose intact.
- The exact visual highlight treatment (background fill, text color, or underline) can be finalized during implementation as long as it remains subtle and readable.
