## ADDED Requirements

### Requirement: Search returns unique documents
The system SHALL return each matching document at most once from search, even when multiple chunks from the same document match the query.

#### Scenario: Multiple matching chunks from one document
- **WHEN** a document has multiple ranked chunks for a query
- **THEN** the search response includes that document only once

### Requirement: Search uses the highest-ranked chunk as representative evidence
The system SHALL include exactly one representative chunk for each returned document, and that chunk MUST be the highest-ranked chunk for that document within the hybrid-scored candidate set.

#### Scenario: Representative chunk is selected deterministically
- **WHEN** multiple chunks from the same document are present in the ranked candidate set
- **THEN** the response includes the chunk with the highest final score for that document
- **AND** ties are resolved deterministically

### Requirement: Search limit applies to documents
The system SHALL apply the search `limit` to unique documents after document deduplication, rather than to raw chunk rows.

#### Scenario: Limit counts unique documents
- **WHEN** search is executed with a positive limit
- **THEN** the response contains at most that many unique documents
- **AND** duplicate documents do not consume additional result slots

### Requirement: Search preserves the existing result shape
The system SHALL preserve the existing search result structure by returning both the selected document and its representative chunk for each result.

#### Scenario: Document-centered result still includes snippet data
- **WHEN** a document is returned by search
- **THEN** the result includes the document data
- **AND** the result includes the representative chunk data for that document
