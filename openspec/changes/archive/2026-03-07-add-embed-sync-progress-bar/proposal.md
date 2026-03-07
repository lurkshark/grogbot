## Why

Bulk embedding via `grogbot search document embed-sync` can take long enough that users do not know whether work is progressing or how much longer it will take. We want the CLI to show progress and an estimated time remaining without pushing terminal UI concerns into `search-core`.

## What Changes

- Add progress reporting to document embedding synchronization so callers can observe per-document completion during a bulk sync run.
- Update the CLI `embed-sync` command to render a progress bar with elapsed time and estimated time remaining while embedding documents.
- Keep progress bar and ETA presentation logic in the CLI package, with `search-core` exposing only optional raw progress callbacks.
- Preserve machine-readable command output by keeping the final JSON result separate from live progress rendering.

## Capabilities

### New Capabilities
- `embedding-sync-progress`: Reports per-document embedding synchronization progress to interactive callers and enables the CLI to display a progress bar with ETA during `embed-sync`.

### Modified Capabilities
- None.

## Impact

- `packages/search-core/src/grogbot_search/service.py` embedding synchronization API and related tests.
- `packages/cli/src/grogbot_cli/app.py` `embed-sync` command UX and output handling.
- `packages/cli/pyproject.toml` if the CLI needs an explicit progress-rendering dependency.
- README or CLI documentation describing progress behavior for bulk embedding.
