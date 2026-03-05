## ADDED Requirements

### Requirement: Embedding generation is explicit and separate from chunk creation
The system SHALL provide embedding operations that generate `chunks_vec` rows from existing plaintext chunks, independent of document upsert and chunk/link generation.

#### Scenario: Upsert does not automatically embed chunks
- **WHEN** a document upsert creates or refreshes plaintext chunks
- **THEN** embedding rows are not created unless an embedding operation is invoked

### Requirement: Embed a single document's chunks
The system SHALL provide a single-document embedding operation that processes one document id and creates missing vector rows for that document's chunks.

#### Scenario: Embedding an existing document
- **WHEN** embedding is requested for a document that exists and has chunks missing vectors
- **THEN** the system creates vector rows for missing chunks and returns the number of vectors created

#### Scenario: Embedding a missing document
- **WHEN** embedding is requested for a document id that does not exist
- **THEN** the system returns a not-found error and creates no vectors

### Requirement: Synchronize embeddings in bulk
The system SHALL provide a bulk embedding synchronization operation that processes documents with missing chunk vectors in stable order and supports an optional maximum document count.

#### Scenario: Bulk embedding sync without maximum
- **WHEN** bulk embedding synchronization runs without a maximum
- **THEN** the system processes all documents with at least one chunk missing a vector and returns total vectors created

#### Scenario: Bulk embedding sync with maximum
- **WHEN** bulk embedding synchronization runs with a maximum of N
- **THEN** the system processes at most N eligible documents in stable order and returns total vectors created

### Requirement: Embedding operations are exposed through API and CLI
The system SHALL expose single-document and bulk embedding synchronization through API and CLI interfaces.

#### Scenario: API embedding request
- **WHEN** a client calls the single-document or bulk embedding API endpoint
- **THEN** the response includes the number of vectors created

#### Scenario: CLI embedding command
- **WHEN** a user runs the single-document or bulk embedding CLI command
- **THEN** the command outputs the number of vectors created
