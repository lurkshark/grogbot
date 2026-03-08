## Why

The current `app` website is visually clean but feels spacious and desktop-leaning, especially on phones where the tall hero layout, pill-shaped controls, and long result snippets consume too much vertical space. We want the web experience to feel like a compact, mobile-first search tool while preserving the existing routes and result ordering behavior.

## What Changes

- Redesign the shared app website chrome to use a thin persistent Grogbot brand stripe across all pages, including `/`, `/search`, and `/search/query`.
- Replace the current roomy hero-style search presentation with a tighter, near-titleless layout and more compact spacing tuned for mobile screens.
- Restyle search inputs and buttons to use lightly rounded rectangular controls instead of fully pill-shaped controls.
- Change search-result snippet presentation to show approximately 120 visible characters instead of the full chunk text.
- Prefer snippets that begin near meaningful literal query-term matches when available, append only a trailing ellipsis when truncated, and visually highlight visible literal query-term matches in the rendered snippet.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `search-web`: Change the HTML app experience to use compact mobile-first layouts, shared top-level branding chrome, and short query-aware highlighted result snippets.

## Impact

- Affects `packages/app/src/grogbot_app/templates/` shared layout and page templates for `/`, `/search`, and `/search/query`.
- Affects `packages/app/src/grogbot_app/static/app.css` responsive layout, spacing, and control styling.
- Affects `packages/app/src/grogbot_app/app.py` result-view formatting for snippets and highlighting.
- Affects `packages/app/tests/test_app.py` HTML rendering expectations for shared chrome, compact search pages, and snippet behavior.
