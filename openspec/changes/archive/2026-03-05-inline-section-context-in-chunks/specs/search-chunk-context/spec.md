## ADDED Requirements

### Requirement: Chunks SHALL inline top-level section context into emitted text
The chunking pipeline SHALL prepend section context to each emitted body chunk using the active heading hierarchy, formatted as plain text with ` > ` separators and no marker token. The context SHALL include at most the top two heading levels from the current heading stack.

#### Scenario: Chunk includes two-level heading context
- **WHEN** body content is chunked under an active `H1` and `H2`
- **THEN** each emitted chunk text begins with `H1 > H2` followed by the chunk body text

#### Scenario: Deep headings are truncated to top two levels
- **WHEN** body content appears under `H1`, `H2`, and deeper headings such as `H3`
- **THEN** emitted chunk context includes only `H1 > H2`

#### Scenario: Single-level context is preserved
- **WHEN** body content has only an active `H1` heading
- **THEN** emitted chunk context begins with only the `H1` text

### Requirement: Chunk size budgeting SHALL be based on body words only
`TARGET_WORDS` and `MAX_WORDS` enforcement SHALL use body-text word counts only and SHALL exclude inline context words from budget accounting.

#### Scenario: Context does not force early chunk split
- **WHEN** body text remains within `MAX_WORDS` but context text is long
- **THEN** the chunk is not split due to context word count

#### Scenario: Context may exceed apparent total words above max
- **WHEN** body text exactly fits the configured limit and context is prepended
- **THEN** emitted chunk text may exceed `MAX_WORDS` in total words while remaining valid

### Requirement: Chunker SHALL avoid heading-only output and mixed-context chunks
The chunker SHALL emit chunks only for body content and SHALL flush active chunk accumulation when heading context changes so one chunk does not mix body from different contexts.

#### Scenario: Heading-only sections produce no standalone chunk
- **WHEN** a heading has no body text before the next heading or document end
- **THEN** no chunk is emitted containing only heading text

#### Scenario: Context transition flushes current chunk
- **WHEN** body has been accumulated under one heading context and a new heading context begins
- **THEN** the current chunk is finalized before accumulating body under the new context

### Requirement: Oversized body fallback SHALL preserve section context
When a body block exceeds `MAX_WORDS` and sentence-group fallback is used, each emitted sentence-group chunk SHALL include the same inherited section context prefix.

#### Scenario: Sentence-split chunks keep identical context
- **WHEN** a large body block is split into multiple chunks by sentence grouping
- **THEN** each emitted chunk begins with the same context path that applied to the oversized block
