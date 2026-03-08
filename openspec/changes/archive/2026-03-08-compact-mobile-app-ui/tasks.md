## 1. Shared page chrome and compact layouts

- [x] 1.1 Move Grogbot branding into shared top-of-page chrome in `packages/app/src/grogbot_app/templates/base.html` so `/`, `/search`, and `/search/query` all render the same brand stripe.
- [x] 1.2 Refactor `packages/app/src/grogbot_app/templates/index.html` into a compact root layout that preserves its entry-point role without the current hero treatment.
- [x] 1.3 Refactor `packages/app/src/grogbot_app/templates/search_landing.html` into a near-titleless compact search-first layout.
- [x] 1.4 Refactor `packages/app/src/grogbot_app/templates/search_results.html` so the query form sits in compact page chrome and renders result snippets from derived display values instead of raw chunk text.

## 2. Styling and mobile density

- [x] 2.1 Update `packages/app/src/grogbot_app/static/app.css` to add the thin shared Grogbot stripe styling and cross-page compact spacing.
- [x] 2.2 Update search input and button styles to use lightly rounded rectangular controls with touch-friendly but denser sizing.
- [x] 2.3 Adjust root, landing, and results layouts for mobile-first behavior, including tighter result spacing and removal of the current large hero feel.
- [x] 2.4 Add snippet highlight styling that is subtle, readable, and visually distinct without overwhelming the result text.

## 3. Snippet formatting and safe highlighting

- [x] 3.1 Add an app-layer helper in `packages/app/src/grogbot_app/app.py` (or a nearby module) that normalizes chunk text and produces compact display snippets of roughly 120 visible characters.
- [x] 3.2 Make snippet generation prefer a start position near the first meaningful literal query-term match and fall back to a clean leading excerpt when no match exists.
- [x] 3.3 Ensure truncated snippets append only a trailing ellipsis and preserve sensible word boundaries where practical.
- [x] 3.4 Add safe server-rendered highlighting for literal query-term matches that appear in the displayed snippet without exposing unescaped HTML.

## 4. Verification

- [x] 4.1 Update `packages/app/tests/test_app.py` to verify shared Grogbot branding chrome appears on `/`, `/search`, and `/search/query`.
- [x] 4.2 Add tests verifying compact result snippets are rendered instead of full chunk text, including truncation and trailing-ellipsis behavior.
- [x] 4.3 Add tests verifying literal query-term matches are highlighted only when visible in the rendered snippet.
- [x] 4.4 Run the relevant app test suite and confirm the updated HTML rendering behavior passes.
