# LanceDB Builder Refactor

## Purpose

Align the Alchemist ingestion flow with the LangChainJS LanceDB vector store builder APIs by avoiding manual table creation via the raw LanceDB connection and instead relying on the LanceDB vector store to manage table creation and reuse.

## Requirements

### Requirement: Use LangChainJS LanceDB configuration
The ingestion flow MUST configure the LangChainJS LanceDB vector store using its supported configuration options (`uri`, `tableName`, `mode`, `textKey`) rather than passing a manually opened `table` instance.

#### Scenario: Vector store initialization
- **WHEN** the ingestion pipeline initializes the LanceDB vector store
- **THEN** it uses the LanceDB vector store configuration options and not a raw LanceDB table

### Requirement: Table creation handled by LanceDB vector store
The ingestion flow MUST allow the LanceDB vector store to create the table when vectors are first added, using its internal `addVectors`/`addDocuments` logic.

#### Scenario: First ingestion run
- **WHEN** the first document is ingested into a new database path
- **THEN** the vector store creates the table with schema inferred from the ingested data

### Requirement: Existing table reuse via LanceDB vector store
The ingestion flow MUST reuse the existing LanceDB table on subsequent runs without manually opening the table through `@lancedb/lancedb` APIs.

#### Scenario: Subsequent ingestion run
- **WHEN** the CLI ingests into a database path that already has a LanceDB table
- **THEN** the vector store reuses the table without direct `connect/openTable` calls

### Requirement: No direct `@lancedb/lancedb` table creation in ingest pipeline
The ingestion pipeline MUST NOT call `connect`, `openTable`, or `createTable` directly.

#### Scenario: Audit of ingestion module
- **WHEN** reviewing the ingestion module for LanceDB usage
- **THEN** there are no direct calls to `@lancedb/lancedb` connection APIs

## Non-Goals

- Changing the CLI interface or embedding model behavior.
- Modifying the stored metadata fields or embedding strategy.
