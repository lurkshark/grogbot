## Why

Alchemist currently bypasses LangChainJS LanceDB helpers and manually creates tables, which risks schema mismatches and diverges from supported vector store behavior. Aligning with the official builder flow ensures consistent table creation and reuse and reduces maintenance risk.

## What Changes

- Update the ingestion pipeline to configure the LanceDB vector store via its supported options (`uri`, `tableName`, etc.) rather than supplying a manually opened table.
- Remove direct `@lancedb/lancedb` connection/table creation calls from `ingest.ts`.
- Allow the vector store to create/reuse the table during `addDocuments`.

## Capabilities

### New Capabilities
- _None_

### Modified Capabilities
- `markdown-processor-db`: Clarify that LanceDB table creation/reuse is handled via LangChainJS vector store configuration without direct `@lancedb/lancedb` calls.

## Impact

- `packages/alchemist/src/ingest.ts` vector store initialization logic.
- Tests that stub the vector store factory may need minor updates.
