## ADDED Requirements

### Requirement: Documents store compact content metadata
The system SHALL persist documents without storing full markdown content and MUST store a `content_hash` field as a 6-character lowercase hexadecimal digest.

#### Scenario: Document is persisted without markdown copy
- **WHEN** a document is created or updated
- **THEN** the persisted document record includes metadata fields and `content_hash`, and does not include a full markdown-content column

#### Scenario: Content hash format is enforced
- **WHEN** a document record is persisted
- **THEN** `content_hash` is exactly 6 characters and contains only lowercase hexadecimal characters (`0-9`, `a-f`)

### Requirement: Upsert refreshes chunks and links based on content hash changes
The system SHALL compute `content_hash` from incoming markdown during upsert and MUST use hash changes to control chunk/link regeneration.

#### Scenario: New document upsert generates chunks and links
- **WHEN** a document is upserted for a canonical URL that does not yet exist
- **THEN** the system stores the document with `content_hash`, creates plaintext chunks, and inserts outbound links derived from the provided markdown

#### Scenario: Changed content hash triggers refresh
- **WHEN** an existing document is upserted and the computed `content_hash` differs from the stored hash
- **THEN** existing chunks and outbound links for that document are deleted and regenerated from the incoming markdown

#### Scenario: Unchanged content hash preserves chunks and links
- **WHEN** an existing document is upserted and the computed `content_hash` matches the stored hash
- **THEN** existing chunks and outbound links are retained and only document metadata updates are applied

### Requirement: Ingestion paths produce chunk-ready documents without embeddings
All ingestion flows that create or update documents SHALL leave the document with current plaintext chunks and links while deferring vector generation to explicit embedding operations.

#### Scenario: URL or feed ingestion creates chunk-ready document
- **WHEN** ingestion creates or updates a document from URL/feed/opml/sitemap content
- **THEN** document metadata, content hash, plaintext chunks, and links are updated in the same ingestion call
- **THEN** no new vector rows are required to be created by that ingestion call
