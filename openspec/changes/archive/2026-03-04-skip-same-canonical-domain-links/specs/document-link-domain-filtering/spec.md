## ADDED Requirements

### Requirement: Outbound link graph SHALL exclude same-canonical-domain targets
When generating outbound document links, the system SHALL compare canonical domains for source and target URLs and MUST skip persistence when both domains are equal.

#### Scenario: Absolute same-domain target is skipped
- **WHEN** a chunked document at `https://example.com/a` contains an outbound link to `https://example.com/b`
- **THEN** no `(from_document_id, to_document_id)` edge is stored for that link

#### Scenario: Cross-domain target is persisted
- **WHEN** a chunked document at `https://example.com/a` contains an outbound link to `https://other.example/b`
- **THEN** one directed edge is stored for the source document and resolved target document id

### Requirement: Relative outbound links MUST be resolved before domain filtering
For outbound links extracted from markdown, the system MUST resolve relative href values against the source document canonical URL before canonicalization and domain comparison.

#### Scenario: Relative internal path is treated as same-domain
- **WHEN** a chunked document at `https://example.com/posts/1` contains `[x](/about)`
- **THEN** the target resolves to `https://example.com/about` for domain comparison and no edge is stored

#### Scenario: Relative traversal path is treated as same-domain
- **WHEN** a chunked document at `https://example.com/posts/1` contains `[x](../archive)`
- **THEN** the resolved target domain matches the source domain and no edge is stored

### Requirement: Cross-domain unknown targets SHALL still derive target ids
After applying same-domain filtering, the system MUST derive `to_document_id` from the canonicalized target URL even when no target document is currently ingested.

#### Scenario: Unknown cross-domain URL stores derived target id
- **WHEN** a chunked document links to `https://external.site/not-ingested` and no document exists for that URL
- **THEN** the system stores the edge with `to_document_id = document_id_for_url(_canonicalize_url("https://external.site/not-ingested"))`
