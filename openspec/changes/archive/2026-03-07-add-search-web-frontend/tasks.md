## 1. Workspace and package setup

- [x] 1.1 Add `packages/web` to the uv workspace and create the package metadata/build configuration.
- [x] 1.2 Create the web package module structure, including the ASGI entrypoint, template directory, and static asset directory.
- [x] 1.3 Add the Python web rendering/static-serving dependencies needed by the new package.

## 2. Root and landing page implementation

- [x] 2.1 Implement the root `/` HTML route for the top-level Grogbot entry page.
- [x] 2.2 Implement the `/search` HTML route with the “Grogbot Search” heading, query input, and Search submit control.
- [x] 2.3 Add the shared base layout and initial CSS needed for the root and search landing pages.

## 3. Search results page integration

- [x] 3.1 Implement the `/search/query` HTML route that reads the `q` parameter and redirects blank or missing queries to `/search`.
- [x] 3.2 Integrate the results route with `SearchService` using the existing configuration/database resolution pattern.
- [x] 3.3 Render the top 25 search results on the results page, preserving service order and allowing duplicate documents.
- [x] 3.4 Add the results-page search box at the top so users can submit a new query from the results screen.

## 4. Verification

- [x] 4.1 Add automated tests for `/`, `/search`, and `/search/query` covering HTML rendering and redirect behavior.
- [x] 4.2 Add automated tests verifying `/search/query` renders up to 25 results and preserves duplicate-document results.
- [x] 4.3 Run the relevant test suite(s) and confirm the new web package works without changing `packages/api`.
