## ADDED Requirements

### Requirement: Search candidate pools use top limit-times-ten rows per method
The search system SHALL, for a query with requested result `limit`, select FTS and vector candidates independently using a candidate depth of `limit * 10`.

#### Scenario: FTS candidate selection
- **WHEN** search evaluates full-text candidates
- **THEN** it selects at most `limit * 10` chunks ordered by `bm25(chunks_fts)` ascending
- **AND** ties are deterministically ordered by `chunk_id` ascending

#### Scenario: Vector candidate selection
- **WHEN** search evaluates vector candidates
- **THEN** it selects at most `limit * 10` chunks ordered by vector `distance` ascending
- **AND** ties are deterministically ordered by `chunk_id` ascending

### Requirement: Reciprocal row-number scoring is applied per retrieval method
The search system SHALL assign row numbers independently for FTS and vector candidate sets using `row_number()` and compute each method score as `1.0 / (1 + row_number)`.

#### Scenario: Row numbering origin
- **WHEN** row numbers are assigned to candidates in either method
- **THEN** numbering starts at 1 for the best-ranked candidate in that method

#### Scenario: Per-method score calculation
- **WHEN** a candidate has row number `n` in a method-specific ranking
- **THEN** that method contributes a score of `1.0 / (1 + n)` for that chunk

### Requirement: Final search score is additive across methods
The search system SHALL compute final chunk score as the sum of method scores and return results ordered by highest final score first.

#### Scenario: Chunk appears in both methods
- **WHEN** a chunk is present in both FTS and vector candidate sets
- **THEN** final score equals `fts_score + vector_score`

#### Scenario: Chunk appears in only one method
- **WHEN** a chunk is present in only one candidate set
- **THEN** missing method score is treated as `0` in the final score sum

#### Scenario: Result limit applied after final ranking
- **WHEN** final scores are computed for all candidate chunks
- **THEN** results are sorted by final score descending
- **AND** only the top `limit` results are returned
