## ADDED Requirements

### Requirement: URL and feed ingestion use a shared cleanup pipeline
The system SHALL run extracted document content from both URL ingestion and feed ingestion through the same cleanup pipeline before prose text is chunked or persisted.

#### Scenario: URL ingestion cleans extracted page content
- **WHEN** a document is created from a fetched HTML page
- **THEN** the extracted main-content HTML is sanitized and normalized before markdown/plaintext chunk inputs are derived

#### Scenario: Feed ingestion cleans entry content
- **WHEN** a document is created from a feed entry with HTML content or summary fields
- **THEN** the entry content is sanitized and normalized through the same cleanup pipeline before markdown/plaintext chunk inputs are derived

### Requirement: Cleanup removes low-signal and unsafe content
The system SHALL remove clearly non-content or low-signal artifacts before chunk creation, including embedded scripts/styles/widgets, comments, unsafe links, malformed control-junk, and other non-prose fragments that do not contribute useful search text.

#### Scenario: Script and widget markup are discarded
- **WHEN** extracted content contains script-like, style-like, or embedded-widget markup
- **THEN** that markup does not appear in persisted chunk text

#### Scenario: Malformed text junk is normalized away
- **WHEN** extracted content contains zero-width characters, control characters, or pathological whitespace noise
- **THEN** the persisted chunk text contains normalized readable text without those artifacts

### Requirement: Ingestion may drop unusable prose blocks
The system SHALL prefer readable natural-language content for indexing and MAY drop extracted blocks that remain clearly low-signal after cleanup instead of forcing them into chunks.

#### Scenario: Generator-style blob is dropped
- **WHEN** an extracted block is dominated by repetitive or non-prose content after cleanup
- **THEN** the system omits that block from chunk text generation

#### Scenario: Document with no usable prose is rejected
- **WHEN** cleanup and filtering leave a document with no usable chunkable text
- **THEN** ingestion fails rather than persisting an effectively empty searchable document
