## ADDED Requirements

### Requirement: Statistics model returns resource counts and computed metrics

The system SHALL provide a `DatasetStatistics` model containing:
- `total_sources`: count of sources in scope
- `total_documents`: count of documents in scope
- `total_chunks`: count of chunks in scope
- `total_links`: count of links in scope
- `embedded_chunks`: count of chunks with embeddings
- `embedding_progress`: percentage (0-100) of chunks with embeddings, 0 if no chunks
- `avg_chunks_per_document`: average chunks per document, 0 if no documents
- `avg_documents_per_source`: average documents per source, 0 if no sources

#### Scenario: Global statistics with populated dataset
- **WHEN** statistics is called without source_id on a dataset with 3 sources, 10 documents, 50 chunks, 25 links, and 40 embedded chunks
- **THEN** the result contains total_sources=3, total_documents=10, total_chunks=50, total_links=25, embedded_chunks=40, embedding_progress=80.0, avg_chunks_per_document=5.0, avg_documents_per_source=3.33...

#### Scenario: Statistics on empty dataset
- **WHEN** statistics is called on an empty database
- **THEN** all counts are 0, embedding_progress=0.0, avg_chunks_per_document=0.0, avg_documents_per_source=0.0

### Requirement: Statistics can be filtered by source

The system SHALL allow filtering statistics by a source_id parameter, narrowing all counts to resources belonging to that source.

#### Scenario: Source-filtered statistics
- **WHEN** statistics is called with source_id="source-A" where source-A has 5 documents, 20 chunks, 8 links, and 15 embedded chunks
- **THEN** the result contains total_sources=1, total_documents=5, total_chunks=20, total_links=8, embedded_chunks=15, embedding_progress=75.0, avg_chunks_per_document=4.0, avg_documents_per_source=5.0

#### Scenario: Non-existent source returns zero counts
- **WHEN** statistics is called with a non-existent source_id
- **THEN** all counts are 0, embedding_progress=0.0, avg_chunks_per_document=0.0, avg_documents_per_source=0.0

### Requirement: Links count reflects outbound links

When filtered by source_id, the system SHALL count only links where `from_document_id` belongs to a document in that source.

#### Scenario: Links scoped to source
- **WHEN** source-A has 3 documents that link to documents in other sources
- **THEN** total_links counts those 3 outbound links, not inbound links from other sources

### Requirement: CLI exposes statistics command

The system SHALL provide a `grogbot search statistics` command that outputs statistics as JSON.

#### Scenario: CLI global statistics
- **WHEN** user runs `grogbot search statistics`
- **THEN** the command outputs JSON with all statistics fields

#### Scenario: CLI source-filtered statistics
- **WHEN** user runs `grogbot search statistics --source-id <id>`
- **THEN** the command outputs JSON with statistics scoped to that source

### Requirement: API exposes statistics endpoint

The system SHALL provide a `GET /search/statistics` endpoint returning statistics as JSON.

#### Scenario: API global statistics
- **WHEN** client requests `GET /search/statistics`
- **THEN** response contains all statistics fields with global counts

#### Scenario: API source-filtered statistics
- **WHEN** client requests `GET /search/statistics?source_id=<id>`
- **THEN** response contains statistics scoped to that source
