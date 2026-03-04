## ADDED Requirements

### Requirement: FastAPI application
The API package SHALL expose a FastAPI application that surfaces search functionality under a `/search` prefix.

#### Scenario: API is importable
- **WHEN** the API package is installed
- **THEN** the FastAPI application can be imported for deployment

### Requirement: Source endpoints
The API MUST provide JSON endpoints to upsert, list, fetch, and delete Sources.

#### Scenario: List sources
- **WHEN** a client sends `GET /search/sources`
- **THEN** the API returns a JSON list of Sources

### Requirement: Document endpoints
The API MUST provide JSON endpoints to upsert, list, fetch, and delete Documents.

#### Scenario: Fetch a document
- **WHEN** a client sends `GET /search/documents/{document_id}`
- **THEN** the API returns the matching Document or a 404

### Requirement: Ingestion endpoints
The API SHALL provide endpoints to ingest from a URL and from an RSS feed.

#### Scenario: Ingest from URL
- **WHEN** a client sends `POST /search/ingest/url` with a URL payload
- **THEN** the API returns the created or updated Document

### Requirement: Query endpoint
The API SHALL provide `GET /search/query?q=<text>` for hybrid search results.

#### Scenario: Query results
- **WHEN** a client requests `/search/query?q=hello+world`
- **THEN** the API returns ranked results in JSON

### Requirement: Config resolution
The API MUST read configuration from `~/.grogbot/config.toml` by default and override it with the path specified in the `GROGBOT_CONFIG` environment variable when set.

#### Scenario: Config override
- **WHEN** `GROGBOT_CONFIG` points to an alternate config file
- **THEN** the API uses that file for settings
