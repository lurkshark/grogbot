## MODIFIED Requirements

### Requirement: Chunking uses bounded target and maximum word sizes
The system SHALL chunk markdown using a target of 512 words and a hard maximum of 1024 words per chunk.

#### Scenario: Chunking targets 512-word groups
- **WHEN** chunking aggregates paragraph blocks under normal flow
- **THEN** the chunker flushes at approximately the 512-word target threshold

#### Scenario: Chunking enforces 1024-word maximum
- **WHEN** adding text to a chunk would exceed 1024 words
- **THEN** the chunker flushes the current chunk and starts a new chunk

#### Scenario: Oversized block is split while honoring 1024-word maximum
- **WHEN** a single block exceeds 1024 words
- **THEN** the chunker splits the block into sentence groups such that each produced chunk is at most 1024 words
