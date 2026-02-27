## ADDED Requirements

### Requirement: Create documents from OPML URL
The search core SHALL provide `create_documents_from_opml` that fetches and parses an OPML document from a URL and ingests documents from feed URLs listed in that OPML.

#### Scenario: OPML ingestion returns documents from multiple feeds
- **WHEN** `create_documents_from_opml` is called with an OPML URL containing multiple valid feed `xmlUrl` entries
- **THEN** the system returns a single flat list of Documents produced by ingesting those feeds

### Requirement: Nested outline feed discovery
The OPML ingestion flow MUST discover feed URLs from nested `<outline>` structures and include any outline node with an `xmlUrl` attribute.

#### Scenario: Nested outline feed URLs are included
- **WHEN** an OPML document contains feed URLs under nested outline nodes
- **THEN** those nested feed URLs are extracted and ingested

### Requirement: Best-effort per-feed processing
OPML ingestion MUST process feed URLs independently so that failure ingesting one feed does not stop ingestion of remaining feeds.

#### Scenario: One feed fails and others still ingest
- **WHEN** an OPML document contains one invalid feed URL and one valid feed URL
- **THEN** ingestion continues after the failed feed and returns Documents from the valid feed

### Requirement: OPML ingestion delegates to feed ingestion
For each extracted feed URL, OPML ingestion MUST call existing `create_documents_from_feed` to preserve feed parsing and document upsert behavior.

#### Scenario: Feed ingestion logic is reused
- **WHEN** OPML ingestion processes a feed URL
- **THEN** the resulting documents are produced through the same feed-ingestion behavior used by direct feed ingestion

### Requirement: OPML ingestion API endpoint
The API SHALL expose OPML ingestion at `POST /search/ingest/opml` accepting a JSON body with `opml_url` and returning the ingested Documents.

#### Scenario: API client ingests OPML URL
- **WHEN** a client POSTs `{ "opml_url": "https://example.com/subscriptions.opml" }` to `/search/ingest/opml`
- **THEN** the API returns a JSON array of Documents generated from successfully processed feeds

### Requirement: OPML ingestion CLI command
The CLI SHALL expose OPML ingestion via `grogbot search ingest-opml <opml_url>` and output the ingested Documents.

#### Scenario: CLI user ingests OPML URL
- **WHEN** a user runs `grogbot search ingest-opml <opml_url>`
- **THEN** the CLI prints a JSON array of Documents generated from successfully processed feeds
