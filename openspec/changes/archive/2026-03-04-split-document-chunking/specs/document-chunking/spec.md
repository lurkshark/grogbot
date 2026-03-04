## ADDED Requirements

### Requirement: Upsert does not create chunks
The system SHALL persist documents without creating chunks during upsert, while deleting existing chunks when content changes.

#### Scenario: Upsert document with changed content
- **WHEN** a document is upserted with different content_markdown
- **THEN** the system deletes existing chunks for that document and does not create new chunks

#### Scenario: Upsert document with unchanged content
- **WHEN** a document is upserted with identical content_markdown
- **THEN** the system retains existing chunks and does not create new chunks

### Requirement: Reject empty document content
The system SHALL reject document upserts where the `content_markdown` is empty after trimming whitespace.

#### Scenario: Upsert with empty content
- **WHEN** a document upsert is attempted with empty or whitespace-only content_markdown
- **THEN** the system returns a validation error and does not persist the document

### Requirement: Chunk a single document
The system SHALL provide a chunking operation that accepts a document id, deletes any existing chunks, creates new chunks from stored markdown, and returns the number of chunks created.

#### Scenario: Chunking an existing document
- **WHEN** chunking is requested for an existing document
- **THEN** the system deletes existing chunks, creates new chunks, and returns the count created

#### Scenario: Chunking a missing document
- **WHEN** chunking is requested for a document id that does not exist
- **THEN** the system returns a not-found error and creates no chunks

### Requirement: Bulk chunking for chunkless documents
The system SHALL provide a bulk chunking operation that finds documents with no chunks, processes them in a stable order, respects an optional maximum document count, and returns the total number of chunks created.

#### Scenario: Bulk chunking without a maximum
- **WHEN** bulk chunking is requested without a maximum
- **THEN** the system chunks every document that has no chunks and returns the total chunks created

#### Scenario: Bulk chunking with a maximum
- **WHEN** bulk chunking is requested with a maximum of N
- **THEN** the system chunks at most N chunkless documents in stable order and returns the total chunks created

### Requirement: Chunking operations are exposed
The system SHALL expose chunking operations for single documents and bulk chunking via API and CLI, returning the chunk count.

#### Scenario: API or CLI chunking request
- **WHEN** a client invokes single-document or bulk chunking via API or CLI
- **THEN** the response includes the count of chunks created
