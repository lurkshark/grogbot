## ADDED Requirements

### Requirement: Paginated feed ingestion
The system SHALL support an optional pagination mode for RSS/Atom feed ingestion, controlled by a `paginate` flag that defaults to `False`.

#### Scenario: Pagination disabled
- **WHEN** feed ingestion is invoked with `paginate` set to `False`
- **THEN** the system ingests entries only from the initial feed page, even if the feed advertises a `rel="next"` link

#### Scenario: Pagination enabled
- **WHEN** feed ingestion is invoked with `paginate` set to `True` and the feed advertises a `rel="next"` link
- **THEN** the system follows `rel="next"` links and ingests entries from subsequent pages until no next link is present, a previously visited feed URL is encountered, or 100 pages have been processed

#### Scenario: Pagination best-effort
- **WHEN** pagination is enabled and a subsequent feed page fails to fetch or parse
- **THEN** the system stops pagination and returns the documents ingested up to that point

### Requirement: OPML pagination propagation
The system SHALL allow OPML ingestion to accept a `paginate` flag (default `False`) and pass it through to feed ingestion for each feed URL.

#### Scenario: OPML pagination enabled
- **WHEN** OPML ingestion is invoked with `paginate` set to `True`
- **THEN** each feed URL extracted from the OPML file is ingested with pagination enabled

### Requirement: Feed ingest interfaces expose pagination
The system SHALL expose the `paginate` flag for feed ingestion via the API and CLI, with defaults of `False`, and the CLI bootstrap flow SHALL enable pagination for feeds.

#### Scenario: API and CLI defaults
- **WHEN** a feed ingestion request is made via the API or CLI without specifying `paginate`
- **THEN** the system treats `paginate` as `False`

#### Scenario: CLI bootstrap enables pagination
- **WHEN** the CLI bootstrap flow ingests feeds from the bootstrap sources
- **THEN** the system invokes feed ingestion with `paginate` set to `True`
