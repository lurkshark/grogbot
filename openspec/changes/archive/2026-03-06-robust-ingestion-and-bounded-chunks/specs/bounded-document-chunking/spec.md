## ADDED Requirements

### Requirement: Chunking remains semantic-first for normal prose
The system SHALL continue to form chunks from prose-oriented document structure, preserving heading context and preferring paragraph/sentence boundaries when content fits within safety limits.

#### Scenario: Normal prose keeps semantic grouping
- **WHEN** document content consists of ordinary paragraphs and headings within configured limits
- **THEN** the system emits context-aware chunks without unnecessary mechanical splitting

### Requirement: Every emitted chunk satisfies absolute safety bounds
The system SHALL enforce absolute chunk safety bounds on the final emitted chunk text, including any prepended context, so no chunk persisted for embedding exceeds the configured hard limits.

#### Scenario: Oversized paragraph is split into safe chunks
- **WHEN** a single prose block would exceed the configured hard limits
- **THEN** the system splits it into multiple chunks such that every emitted chunk satisfies those limits

#### Scenario: Oversized single sentence cannot bypass limits
- **WHEN** a punctuation-poor or single-sentence block exceeds the configured hard limits
- **THEN** the system applies fallback splitting beyond sentence boundaries until every emitted chunk satisfies those limits

### Requirement: Chunking uses fallback split stages for pathological content
The system SHALL apply progressively more mechanical fallback splitting for oversized content after semantic splitting is exhausted.

#### Scenario: Line-oriented fallback split
- **WHEN** sentence-based splitting is insufficient to bound an oversized block
- **THEN** the system attempts an intermediate fallback split using simpler internal boundaries before resorting to fixed-size windows

#### Scenario: Final hard-window fallback
- **WHEN** no semantic or delimiter-based split can produce a safe chunk
- **THEN** the system emits only hard-bounded fixed-size chunks or drops the remaining content

### Requirement: Chunking may discard persistently low-signal oversized content
The system SHALL allow pathological content to be dropped instead of persisted when it cannot be transformed into useful prose-oriented chunks.

#### Scenario: Low-quality oversized block is omitted
- **WHEN** an oversized block remains clearly low-signal after cleanup and fallback evaluation
- **THEN** the system omits that block from persisted chunks
