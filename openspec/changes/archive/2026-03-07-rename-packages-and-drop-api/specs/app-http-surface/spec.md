## ADDED Requirements

### Requirement: The app is the only remaining HTTP package
The repository SHALL provide `packages/app` as the only active HTTP-serving package, and the standalone `packages/api` package SHALL be absent from the active workspace.

#### Scenario: A contributor inspects the active HTTP surfaces
- **WHEN** a contributor inspects the active workspace packages and package metadata
- **THEN** they find `packages/app` as the browser-facing HTTP package
- **AND** they do not find an active `packages/api` workspace package or `grogbot-api` distribution

### Requirement: The active HTTP surface is browser-facing rather than JSON API based
The `grogbot_app` package SHALL expose the server-rendered browser routes and static assets needed by the existing app experience, and the active repository SHALL not expose standalone JSON HTTP endpoints for search CRUD, ingestion, embedding, statistics, or query operations.

#### Scenario: A contributor runs the app locally
- **WHEN** a contributor starts the active HTTP package locally
- **THEN** the app serves the browser-facing routes for the landing page and search experience
- **AND** the app serves its static assets
- **AND** the active repository does not provide standalone JSON HTTP endpoints for source CRUD, document CRUD, ingestion, embedding, statistics, or query responses
