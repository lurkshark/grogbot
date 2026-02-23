## MODIFIED Requirements

### Requirement: LanceDB storage via LangChainJS vector store
The system MUST store embeddings and corresponding post content in a local-file LanceDB database using the LangChainJS vector store interface without directly managing LanceDB tables.

#### Scenario: Persisting vectors and content
- **WHEN** embeddings are generated for a markdown file
- **THEN** the vector and associated post content are persisted to LanceDB through the LangChainJS vector store using configuration options (e.g., `uri`, `tableName`) rather than direct `@lancedb/lancedb` table operations

### Requirement: Deterministic local vector database initialization
The CLI SHALL initialize the local-file LanceDB database using the LangChainJS vector store configuration each run, even if that recreates the table.

#### Scenario: Subsequent ingestion run
- **WHEN** the CLI is run again against a directory
- **THEN** it initializes the LanceDB table using LangChainJS configuration without manual table open/create calls, allowing the table to be recreated as needed
