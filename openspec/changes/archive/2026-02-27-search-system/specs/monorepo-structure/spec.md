## ADDED Requirements

### Requirement: uv workspace layout
The repository SHALL be structured as a uv workspace with a top-level `pyproject.toml` and member packages located under `packages/`.

#### Scenario: Workspace packages are discoverable
- **WHEN** a developer lists workspace members
- **THEN** the workspace includes `packages/search-core`, `packages/cli`, and `packages/api`

### Requirement: Package separation
The search core, CLI, and API components MUST live in separate packages with independent dependencies and entry points.

#### Scenario: Isolation of dependencies
- **WHEN** the CLI package is installed
- **THEN** it depends on the search core package but not the API package
