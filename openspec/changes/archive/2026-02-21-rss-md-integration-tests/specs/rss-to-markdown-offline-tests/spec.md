## ADDED Requirements

### Requirement: Offline integration-style test coverage
The test suite MUST execute the RSS-to-markdown workflow end-to-end using repository-local fixtures and MUST NOT require network access.

#### Scenario: Run tests without internet
- **WHEN** the offline integration tests are executed in an environment without network access
- **THEN** the tests complete successfully using only repository-local fixture data

### Requirement: Repository-local fixture inputs and outputs
The tests MUST read RSS input fixtures and expected Markdown outputs from within the repository and MUST NOT access files outside the project directory.

#### Scenario: Validate fixture locations
- **WHEN** the offline integration tests resolve fixture paths
- **THEN** the inputs and expected outputs are loaded from paths within the repository

### Requirement: Representative feed variants
The tests MUST cover at least one typical RSS feed and one feed with missing optional fields to validate parsing and Markdown formatting behavior.

#### Scenario: Typical feed conversion
- **WHEN** a standard RSS fixture is processed
- **THEN** the generated Markdown matches the expected fixture output

#### Scenario: Missing optional fields
- **WHEN** a feed fixture omits optional fields
- **THEN** the generated Markdown matches the expected fixture output and required frontmatter remains present
