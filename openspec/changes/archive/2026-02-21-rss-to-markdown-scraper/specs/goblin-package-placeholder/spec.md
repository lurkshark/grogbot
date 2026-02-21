## MODIFIED Requirements

### Requirement: Goblin placeholder package
The repository SHALL include a workspace package named `@grogbot/goblin` that provides the RSS-to-markdown CLI tool.

#### Scenario: Workspace recognizes goblin package
- **WHEN** a developer lists workspace packages
- **THEN** the `@grogbot/goblin` package is included in the workspace

### Requirement: Goblin package entry point
The `@grogbot/goblin` package SHALL define a TypeScript entry point and a CLI `bin` entry suitable for invoking the RSS-to-markdown tool.

#### Scenario: Build goblin package
- **WHEN** the `@grogbot/goblin` package is compiled
- **THEN** the entry point is included in the compiled output according to the package configuration

#### Scenario: Execute goblin CLI
- **WHEN** the CLI is invoked via the package `bin`
- **THEN** the RSS-to-markdown tool runs with the provided arguments
