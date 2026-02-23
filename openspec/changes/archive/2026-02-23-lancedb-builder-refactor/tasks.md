## 1. Update LanceDB initialization

- [x] 1.1 Replace manual `@lancedb/lancedb` connection logic in `packages/alchemist/src/ingest.ts` with LangChainJS `LanceDB` configuration options (`uri`, `tableName`, optionally `mode`).
- [x] 1.2 Remove direct `connect/openTable/createTable` usage from the ingestion pipeline.

## 2. Validate behavior and tests

- [x] 2.1 Ensure ingestion still writes to the same db path and table name, and table creation happens through `addDocuments`.
- [x] 2.2 Update/extend tests if needed to reflect the new vector store initialization behavior.
