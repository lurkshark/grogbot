## ADDED Requirements

### Requirement: Bulk embedding synchronization reports per-document progress to callers

The system SHALL allow `synchronize_document_embeddings` callers to provide an optional progress callback that receives raw synchronization progress for the selected documents in the current run.

#### Scenario: Initial progress snapshot reflects selected work
- **WHEN** bulk embedding synchronization starts for 12 pending documents
- **THEN** the callback receives an initial progress snapshot with total selected documents set to 12 and completed documents set to 0

#### Scenario: Progress advances after each completed document
- **WHEN** bulk embedding synchronization completes embedding the next pending document
- **THEN** the callback receives an updated snapshot showing one additional completed document and the cumulative vectors created so far

#### Scenario: Maximum limits the reported total
- **WHEN** more than 100 documents are pending and synchronization is invoked with `maximum=100`
- **THEN** the callback reports totals for the 100 selected documents in that run rather than all pending documents in the database

### Requirement: CLI embed-sync shows progress and ETA during synchronization

The `grogbot search document embed-sync` command SHALL display live progress for the current bulk embedding run, including completed documents, total selected documents, and an estimated time remaining.

#### Scenario: CLI shows progress for a multi-document run
- **WHEN** a user runs `grogbot search document embed-sync` for a synchronization run with pending documents
- **THEN** the command shows a live progress indicator while documents are being embedded
- **AND** the progress indicator includes the total selected documents and completed documents
- **AND** the progress indicator includes an estimated time remaining derived from observed progress

#### Scenario: CLI initializes progress before the first document finishes
- **WHEN** a synchronization run starts and documents have been selected but no document has completed yet
- **THEN** the CLI shows progress initialized at 0 completed documents out of the selected total

### Requirement: CLI progress rendering preserves structured command output

The `grogbot search document embed-sync` command SHALL keep live progress output separate from its final machine-readable result.

#### Scenario: Final JSON remains machine-readable
- **WHEN** a synchronization run completes
- **THEN** the command outputs the final `{ "vectors_created": <count> }` result without embedded progress-bar control sequences in stdout

#### Scenario: Progress does not replace the final result
- **WHEN** a user runs `grogbot search document embed-sync`
- **THEN** the command displays live progress during execution
- **AND** the command still emits the final structured result after synchronization completes
