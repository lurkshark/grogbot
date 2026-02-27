## ADDED Requirements

### Requirement: Grogbot CLI entrypoint
The CLI package SHALL provide a `grogbot` Typer application with a `search` command group.

#### Scenario: CLI entrypoint is available
- **WHEN** the CLI package is installed
- **THEN** the `grogbot` command is available on the PATH

### Requirement: Search subcommands
The `grogbot search` group MUST expose subcommands for managing sources, documents, ingestion, and querying.

#### Scenario: Source management commands
- **WHEN** a user runs `grogbot search source --help`
- **THEN** the CLI lists subcommands for upsert, list, get, and delete

### Requirement: Query command
The CLI SHALL provide `grogbot search query <text>` to execute hybrid search and return ranked results.

#### Scenario: Query output
- **WHEN** `grogbot search query "hello world"` is executed
- **THEN** the CLI returns ranked results for the query

### Requirement: Ingestion commands
The CLI SHALL provide commands to ingest documents from URLs and RSS feeds.

#### Scenario: URL ingestion command
- **WHEN** a user runs `grogbot search ingest-url <url>`
- **THEN** a Document is created or updated from that URL

### Requirement: Config resolution
The CLI MUST read configuration from `~/.grogbot/config.toml` by default and override it with the path specified in the `GROGBOT_CONFIG` environment variable when set.

#### Scenario: Config override
- **WHEN** `GROGBOT_CONFIG` points to an alternate config file
- **THEN** the CLI uses that file for settings

### Requirement: Structured output
Commands that return data SHALL emit structured JSON to stdout representing the created, updated, or queried resources.

#### Scenario: JSON response
- **WHEN** a Source is upserted via the CLI
- **THEN** the CLI prints a JSON representation of the Source
