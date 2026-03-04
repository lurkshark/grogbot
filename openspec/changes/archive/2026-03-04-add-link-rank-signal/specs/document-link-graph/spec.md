## ADDED Requirements

### Requirement: Outbound document links SHALL be stored as unique directed pairs
The system SHALL persist document links as directed `(from_document_id, to_document_id)` pairs, and it MUST prevent duplicate pairs from the same source document to the same target document.

#### Scenario: Multiple links to the same target in one document
- **WHEN** a document contains multiple outbound links that resolve to the same target URL
- **THEN** the system stores exactly one link pair for that `(from_document_id, to_document_id)` relationship

#### Scenario: Links to different targets from one document
- **WHEN** a document contains outbound links that resolve to different target URLs
- **THEN** the system stores one link pair per unique target document id

### Requirement: Link targets SHALL be derived even when target documents are not ingested
For each outbound link extracted from document content, the system SHALL canonicalize the URL and MUST derive `to_document_id` via `document_id_for_url` regardless of whether a corresponding `documents` row exists.

#### Scenario: Outbound link points to unknown target URL
- **WHEN** a chunked document links to a URL that has not been ingested as a document
- **THEN** the system stores a link pair using `to_document_id = document_id_for_url(_canonicalize_url(url))`

### Requirement: Outbound links SHALL follow chunk lifecycle and ignore self-links
The system SHALL refresh outbound links for a document during `chunk_document(document_id)` by deleting existing links from that document and inserting links extracted from current content. The system MUST delete outbound links from a document when its content changes or the document is deleted. The system MUST ignore self-links where `from_document_id == to_document_id`.

#### Scenario: Chunking regenerates outbound links from current content
- **WHEN** `chunk_document(document_id)` is invoked for a document with previously stored outbound links
- **THEN** existing links from that document are deleted before new outbound links are inserted

#### Scenario: Content change clears stale outbound links before re-chunking
- **WHEN** `upsert_document` updates an existing document with changed `content_markdown`
- **THEN** all links where `from_document_id` equals that document id are deleted

#### Scenario: Self-links are excluded
- **WHEN** an outbound link resolves to the same document id as the source document
- **THEN** the system does not store that link pair