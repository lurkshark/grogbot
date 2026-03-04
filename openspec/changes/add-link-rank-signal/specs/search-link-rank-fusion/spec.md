## ADDED Requirements

### Requirement: Search SHALL include a link-based reciprocal-rank signal
The search ranking pipeline SHALL compute a `link_score` channel from inbound-link counts and MUST add it to existing reciprocal FTS and vector scores with equal weight.

#### Scenario: Final score includes all three signals
- **WHEN** a query returns ranked chunk candidates
- **THEN** each result score is computed as `score = fts_score + vector_score + link_score`

### Requirement: Link score SHALL rank by inbound links and zero-fill missing link authority
For ranked candidate documents with one or more inbound links, the system SHALL assign link row numbers ordered by inbound link count descending and document id ascending for deterministic ties, and MUST compute `link_score = 1.0 / (1 + row_number)`. Documents with zero inbound links MUST receive `link_score = 0.0`.

#### Scenario: Document with inbound links gets reciprocal link score
- **WHEN** a candidate document has at least one inbound link and ranks first among candidate documents by inbound count
- **THEN** its `link_score` is `1.0 / (1 + 1)`

#### Scenario: Document without inbound links gets zero link score
- **WHEN** a candidate document has zero inbound links
- **THEN** its `link_score` is `0.0`

### Requirement: Search results SHALL expose link_score
The search result model SHALL include `link_score` for every returned result, alongside `fts_score`, `vector_score`, and final `score`.

#### Scenario: Query response contains link_score field
- **WHEN** search results are returned from the service
- **THEN** each result includes a numeric `link_score` field