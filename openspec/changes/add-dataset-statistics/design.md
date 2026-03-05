## Context

The search system uses SQLite with sqlite-vec for vector embeddings. Data is organized into sources → documents → chunks, with links tracking cross-document relationships. Currently, users have no visibility into aggregate statistics without directly querying the database.

The statistics feature provides counts and computed metrics, optionally scoped to a single source.

## Goals / Non-Goals

**Goals:**
- Expose resource counts (sources, documents, chunks, links) via CLI and API
- Show embedding progress (chunks with vectors vs total chunks)
- Support filtering by source_id to narrow statistics to a specific source
- Compute derived metrics (embedding progress %, avg chunks per document, documents per source)

**Non-Goals:**
- Historical statistics or trend tracking
- Per-source breakdown in a single call (user must call multiple times with different source_ids)
- Real-time updates (statistics are point-in-time snapshots)

## Decisions

### 1. Single SQL transaction for all counts

**Decision:** Execute all count queries in a single transaction for consistency.

**Rationale:** Statistics should represent a consistent snapshot. Without a transaction, counts could shift between queries if ingestion is running concurrently.

**Alternatives considered:**
- Separate queries: Could show inconsistent state (e.g., chunks without corresponding documents during deletion)

### 2. Embedding progress as percentage (0-100)

**Decision:** Return `embedding_progress` as a float between 0-100.

**Rationale:** Matches user intuition for "progress" and aligns with common progress bar conventions.

**Alternatives considered:**
- 0-1 float: Less intuitive for display
- Fraction (embedded/total): Requires UI to compute percentage

### 3. Links count scoped to outbound links from source

**Decision:** When filtering by source_id, count only links where `from_document_id` belongs to that source.

**Rationale:** Matches the natural interpretation of "links from this source." Inbound links from other sources would require cross-source awareness that's less useful for source-scoped monitoring.

**Alternatives considered:**
- Count all links involving source's documents (both directions): More complex, less clear semantics
- Ignore links when source-scoped: Loses valuable information

### 4. Division by zero returns 0

**Decision:** All computed percentages return 0 when denominator is 0.

**Rationale:** Simpler than returning None and forces caller to handle nullability. An empty dataset has "no progress" rather than "undefined progress."

## Risks / Trade-offs

**Large datasets could cause slow queries** → Queries use COUNT(*) which SQLite optimizes well. For extremely large datasets, consider caching or async computation in the future.

**Statistics can become stale during heavy ingestion** → This is acceptable since statistics are point-in-time. Users can poll if they need updates.
