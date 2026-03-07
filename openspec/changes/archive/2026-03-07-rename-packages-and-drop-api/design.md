## Context

The repository currently presents four workspace packages: `search-core`, `cli`, `api`, and `web`. Their naming is inconsistent across directory names, distribution names, and Python module names: `search-core` already imports as `grogbot_search`, while the web frontend uses `grogbot_web` even though its role is the main browser-facing application. The standalone `api` package is also a thin FastAPI wrapper over `SearchService`, while the newer web frontend already talks directly to the same core service.

This change touches workspace metadata, package metadata, Python import paths, developer commands, tests, and runtime HTTP surfaces. It is also intentionally breaking: package identities change and the JSON HTTP surface disappears.

## Goals / Non-Goals

**Goals:**
- Establish a single canonical naming pattern of `packages/<name>` → `grogbot-<name>` → `grogbot_<name>` where appropriate.
- Rename `search-core` to `search` while preserving the existing `grogbot_search` Python module.
- Rename `web` to `app` and `grogbot_web` to `grogbot_app` so the browser-facing surface is described consistently.
- Remove the standalone `api` package and all JSON HTTP endpoints.
- Update current workspace metadata, tests, and documentation so the new names are the only active names moving forward.
- Explicitly document that archived OpenSpec artifacts may still mention the historical package names.

**Non-Goals:**
- Rebranding the project name from Grogbot to a shorter form.
- Changing the `grogbot_search` module name.
- Adding replacement JSON API routes inside `grogbot_app`.
- Rewriting archived OpenSpec artifacts to retroactively match the new repository structure.
- Changing search behavior, storage, or HTML page behavior beyond import/package identity updates.

## Decisions

### 1. Adopt an exact rename map for active packages

The active workspace packages will become:

- `packages/search` → distribution `grogbot-search` → module `grogbot_search`
- `packages/cli` → distribution `grogbot-cli` → module `grogbot_cli`
- `packages/app` → distribution `grogbot-app` → module `grogbot_app`

`grogbot_search` remains unchanged because it already matches the desired import naming pattern and is used broadly by the CLI and app.

**Rationale:** This yields a predictable rule for contributors: directory, distribution, and module names line up as closely as Python packaging allows.

**Alternatives considered:**
- Keep `grogbot-search-core` while only renaming the directory: rejected because it preserves the current mismatch.
- Rename the core Python module to `grogbot_search_core`: rejected because it adds churn without improving clarity.

### 2. Remove the standalone API package instead of folding its JSON routes into the app

The repository will no longer ship a separate `packages/api` package or its `grogbot-api` distribution. The app remains the only HTTP package and continues to serve the browser-facing HTML/static routes.

**Rationale:** The product direction is now CLI + server-rendered app. Keeping a separate JSON HTTP surface adds maintenance and naming overhead without serving the intended product shape.

**Alternatives considered:**
- Keep the API package for future use: rejected because it keeps unused package structure alive.
- Move the JSON routes into `grogbot_app`: rejected because the desired end state is zero JSON HTTP endpoints, not a relocated API.

### 3. Treat archived OpenSpec references as historical, not normative

Archived change artifacts may continue to reference `packages/search-core`, `packages/web`, and `packages/api`. The new proposal/spec/design set will explicitly state that those references describe the repository at the time of those archived changes and should not be read as the current canonical layout.

**Rationale:** Archive integrity is more valuable than retroactive textual consistency, and changing archived artifacts would blur historical context.

**Alternatives considered:**
- Rewrite archived artifacts to match current names: rejected because it distorts the historical record.

### 4. Update workspace metadata and verification paths in one coordinated sweep

The implementation should update the root workspace configuration, package `pyproject.toml` files, Python import paths, test imports, README commands, and lockfile/package references together.

**Rationale:** Partial renames are brittle in a uv workspace; coordinated updates minimize broken editable installs, stale lockfile entries, and mismatched developer commands.

**Alternatives considered:**
- Rename directories first and defer metadata/docs changes: rejected because it leaves the workspace in an inconsistent and confusing state.

## Risks / Trade-offs

- **[Risk] Existing consumers or scripts may still use `grogbot-search-core`, `grogbot-web`, or `grogbot-api` names** → **Mitigation:** mark the change as breaking and update current documentation/commands everywhere in-repo.
- **[Risk] Import-path churn around `grogbot_web` → `grogbot_app` may leave stale test or runtime references** → **Mitigation:** update all current imports, package metadata, and tests together and verify the app package imports cleanly.
- **[Risk] Removing the API package may surprise future readers because archived docs still mention API work** → **Mitigation:** add an explicit historical-note requirement in this change’s specs and current documentation.
- **[Trade-off] A future programmatic HTTP API would need to be reintroduced intentionally rather than already existing in dormant form** → **Mitigation:** accept this simplification now; if requirements change later, propose a new capability explicitly.

## Migration Plan

1. Rename workspace directories from `search-core` to `search` and `web` to `app`.
2. Update root workspace membership and source definitions to use `grogbot-search` and `grogbot-app`, and remove API package references.
3. Rename the web module package from `grogbot_web` to `grogbot_app` and update all imports/tests/docs accordingly.
4. Delete `packages/api` and remove all in-repo references to its package name, startup commands, and JSON endpoints from current documentation.
5. Regenerate the lockfile and validate package-oriented commands against the renamed workspace packages.

## Open Questions

- None currently. The target package names, HTTP-surface decision, and archive treatment are all decided.
