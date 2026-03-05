## MODIFIED Requirements

### Requirement: SearchService embedding operations use canonical method names
The service SHALL expose canonical embedding operations via `embed_document_chunks` and `synchronize_document_embeddings` without backward-compatible alias methods.

#### Scenario: Single-document embedding uses canonical method
- **WHEN** callers request embedding for one document
- **THEN** they invoke `embed_document_chunks(document_id)`

#### Scenario: Bulk embedding sync uses canonical method
- **WHEN** callers request bulk synchronization of missing vectors
- **THEN** they invoke `synchronize_document_embeddings(maximum=...)`

#### Scenario: Backward-compatible aliases are removed
- **WHEN** consumers inspect or call service embedding aliases
- **THEN** `chunk_document` and `synchronize_document_chunks` are not part of the supported service API
