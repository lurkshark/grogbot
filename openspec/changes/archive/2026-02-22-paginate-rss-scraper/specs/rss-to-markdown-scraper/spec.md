## MODIFIED Requirements

### Requirement: RSS feed ingestion
The CLI SHALL accept an RSS feed URL and parse the feed into individual posts. The CLI MUST also support processing RSS input from repository-local fixtures so that the workflow can be executed without network access. For Blogger and WordPress feeds, the CLI MUST paginate through feed pages until either all posts are retrieved or a configurable maximum post limit is reached. The maximum post limit MUST default to 100 posts and MUST be configurable via an optional command line parameter.

#### Scenario: Parse feed into posts
- **WHEN** the user runs the CLI with a valid RSS feed URL
- **THEN** the tool parses the feed and identifies each post item for export

#### Scenario: Parse repository-local feed fixture
- **WHEN** the CLI is executed against a repository-local RSS fixture
- **THEN** the tool parses the feed and identifies each post item for export without network access

#### Scenario: Paginate Blogger feed until completion
- **WHEN** the CLI ingests a Blogger RSS feed that spans multiple pages
- **THEN** the tool follows pagination links until all posts are collected or the maximum post limit is reached

#### Scenario: Paginate WordPress feed until completion
- **WHEN** the CLI ingests a WordPress RSS feed that spans multiple pages
- **THEN** the tool follows pagination links until all posts are collected or the maximum post limit is reached

#### Scenario: Use default maximum post limit
- **WHEN** the CLI is executed without a maximum post limit parameter
- **THEN** the tool stops pagination after exporting 100 posts

#### Scenario: Override maximum post limit
- **WHEN** the user provides a maximum post limit parameter
- **THEN** the tool stops pagination after exporting the specified number of posts
