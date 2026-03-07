## ADDED Requirements

### Requirement: Canonical workspace package identities
The repository SHALL define the active Grogbot workspace packages using a consistent naming pattern between directory names, distribution names, and Python module names. The active package set SHALL be `packages/search` / `grogbot-search` / `grogbot_search`, `packages/cli` / `grogbot-cli` / `grogbot_cli`, and `packages/app` / `grogbot-app` / `grogbot_app`.

#### Scenario: Active package layout is inspected
- **WHEN** a contributor inspects the current workspace configuration and package metadata
- **THEN** they find `search`, `cli`, and `app` as the active package directories
- **AND** the corresponding active workspace distribution names are `grogbot-search`, `grogbot-cli`, and `grogbot-app`
- **AND** the Python modules are `grogbot_search`, `grogbot_cli`, and `grogbot_app`

### Requirement: Current repository documentation uses canonical package names
Current repository documentation and package-oriented developer commands SHALL use the active package names and paths rather than the retired `search-core`, `web`, and `api` names.

#### Scenario: A contributor follows current setup or run documentation
- **WHEN** a contributor reads current repository documentation for syncing dependencies, running tests, or starting the browser app
- **THEN** the documented package names and paths use `packages/search`, `packages/cli`, and `packages/app`
- **AND** the documented `uv run --package ...` commands use `grogbot-search`, `grogbot-cli`, and `grogbot-app`

### Requirement: Archived naming references remain historical
Archived OpenSpec artifacts SHALL be treated as historical records and MAY retain references to the retired `search-core`, `web`, and `api` names, while current change artifacts and current repository documentation SHALL identify those references as historical rather than canonical.

#### Scenario: A contributor encounters old package names in archived artifacts
- **WHEN** a contributor reads archived OpenSpec artifacts that mention `packages/search-core`, `packages/web`, or `packages/api`
- **THEN** the current change artifacts describe those names as historical references
- **AND** the contributor can determine that the canonical current package layout is `search`, `cli`, and `app`
