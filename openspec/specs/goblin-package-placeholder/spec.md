## Purpose

Define the initial placeholder package for the `goblin` tool within the monorepo.

## Requirements

### Requirement: Goblin placeholder package
The repository SHALL include a workspace package named `goblin` as a placeholder for a future RSS-to-markdown tool.

#### Scenario: Workspace recognizes goblin package
- **WHEN** a developer lists workspace packages
- **THEN** the `goblin` package is included in the workspace

### Requirement: Goblin package entry point
The `goblin` package SHALL define a TypeScript entry point suitable for future implementation.

#### Scenario: Build goblin package
- **WHEN** the `goblin` package is compiled
- **THEN** the entry point is included in the compiled output according to the package configuration
