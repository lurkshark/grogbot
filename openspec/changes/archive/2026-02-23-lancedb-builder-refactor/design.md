## Context

Alchemist ingestion currently constructs a LanceDB vector store by manually opening or creating a LanceDB table using `@lancedb/lancedb` and passing that table into LangChainJS `LanceDB`. This bypasses the vector store’s built-in table creation flow, which creates tables on first add and infers schema from data. The proposal aims to align with LangChainJS’s supported configuration (`uri`, `tableName`, `mode`, `textKey`) and rely on its lifecycle behavior.

## Goals / Non-Goals

**Goals:**
- Configure the LanceDB vector store using LangChainJS options instead of passing a raw table.
- Remove direct `connect/openTable/createTable` usage from the ingestion pipeline.
- Preserve existing CLI behavior (same db path, table name, embeddings, metadata fields).

**Non-Goals:**
- Changing CLI arguments or defaults.
- Altering embedding generation, metadata schema, or storage format beyond what LangChainJS already does.
- Introducing new ingestion modes or migrations.

## Decisions

- **Use LangChainJS configuration (`uri`, `tableName`) in `vectorStoreFactory`.**
  - *Why:* LangChainJS supports lazy table creation on first add, avoiding manual schema creation with empty datasets.
  - *Alternatives considered:*
    - Keep manual table creation and pass `table` to the vector store. Rejected due to schema inference risk and divergence from supported path.

- **Rely on `addDocuments` to create the table on first ingest.**
  - *Why:* LangChainJS `LanceDB` creates the table with actual data, ensuring vector/metadata schema is inferred correctly.
  - *Alternatives considered:* Explicitly create the table with a schema upfront. Rejected as unnecessary and more complex.

- **Keep the same table name (`markdown_posts`) and db path (`./lancedb`).**
  - *Why:* Avoid breaking existing usage or storage locations.

## Risks / Trade-offs

- **Table creation mode defaults to `overwrite`.**
  - *Risk:* Using `overwrite` recreates the table on each run, clearing prior entries.
  - *Mitigation:* Accept this behavior for now to avoid direct `@lancedb/lancedb` usage; document that ingestion resets the table each run.

- **Behavior divergence from current manual creation.**
  - *Risk:* The schema inferred by LangChainJS may differ from manual empty-table creation, potentially affecting downstream queries.
  - *Mitigation:* Validate ingestion output in integration tests or manual runs.
