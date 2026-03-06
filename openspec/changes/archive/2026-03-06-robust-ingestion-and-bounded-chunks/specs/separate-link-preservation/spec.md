## ADDED Requirements

### Requirement: Outbound links are preserved independently from prose pruning
The system SHALL extract outbound links from cleaned source content independently from the prose-chunk generation path so useful links can survive aggressive text filtering.

#### Scenario: Link survives dropped prose block
- **WHEN** a cleaned content block contains a valid outbound link but its surrounding text is dropped as low-signal
- **THEN** the outbound link is still considered for document-link persistence

### Requirement: Link extraction uses cleaned source content
The system SHALL derive document links from cleaned source content rather than from already-pruned chunk text alone.

#### Scenario: Links are available before chunk filtering
- **WHEN** ingestion processes cleaned source content that includes valid links
- **THEN** link extraction runs on that cleaned source representation before prose-only chunk filtering determines persisted chunk text

### Requirement: Link preservation keeps existing link-safety behavior
The system SHALL preserve only valid canonicalizable links after cleanup and SHALL continue to ignore links that are unsafe or not eligible for the link graph.

#### Scenario: Unsafe link is ignored
- **WHEN** cleaned content contains a `javascript:` or similarly unsafe link target
- **THEN** that link is not persisted in the document-link graph

#### Scenario: Relative link remains eligible after cleanup
- **WHEN** cleaned content contains a relative link that resolves to an eligible outbound target
- **THEN** the system resolves, canonicalizes, and persists the link according to normal link-graph rules
