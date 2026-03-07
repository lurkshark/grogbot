## Why

The workspace package layout and distribution names are inconsistent today: `packages/search-core` publishes `grogbot-search-core` while the importable module is already `grogbot_search`, and the web frontend uses `web`/`grogbot-web`/`grogbot_web` instead of the clearer `app` naming used elsewhere. The repository also still carries a standalone JSON API package even though the intended product surfaces are now the CLI and the server-rendered app.

## What Changes

- Rename `packages/search-core` to `packages/search` while keeping the Python module name `grogbot_search` and renaming the published workspace package to `grogbot-search`.
- Rename `packages/web` to `packages/app`, rename the published workspace package from `grogbot-web` to `grogbot-app`, and rename the Python module from `grogbot_web` to `grogbot_app`.
- **BREAKING** Remove the standalone `packages/api` package, its `grogbot-api` distribution, and all JSON HTTP endpoints it exposes.
- Update workspace metadata, developer commands, tests, and current documentation to use the renamed packages as the canonical repository structure.
- Document that archived OpenSpec artifacts may continue to mention the historical `search-core`, `web`, and `api` names and should be read as historical context rather than the current package layout.

## Capabilities

### New Capabilities
- `workspace-package-structure`: Defines the canonical workspace directories, distribution names, module names, and how current docs should describe them.
- `app-http-surface`: Defines the remaining browser-facing HTTP surface after the standalone JSON API is removed.

### Modified Capabilities
- None.

## Impact

- Affected code: root `pyproject.toml`, `uv.lock`, `README.md`, package `pyproject.toml` files, app module imports/tests, and removal of `packages/api`.
- Affected developer workflows: `uv sync`, `uv run --package ...`, local app startup commands, and package-oriented test commands.
- Affected runtime/API surface: the standalone JSON FastAPI service is removed; only the server-rendered app HTTP surface remains.
