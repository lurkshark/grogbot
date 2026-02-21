## MODIFIED Requirements

### Requirement: RSS feed ingestion
The CLI SHALL accept an RSS feed URL and parse the feed into individual posts. The CLI MUST also support processing RSS input from repository-local fixtures so that the workflow can be executed without network access.

#### Scenario: Parse feed into posts
- **WHEN** the user runs the CLI with a valid RSS feed URL
- **THEN** the tool parses the feed and identifies each post item for export

#### Scenario: Parse repository-local feed fixture
- **WHEN** the CLI is executed against a repository-local RSS fixture
- **THEN** the tool parses the feed and identifies each post item for export without network access
