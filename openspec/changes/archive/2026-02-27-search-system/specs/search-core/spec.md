## ADDED Requirements

### Requirement: Core data models
The search core package SHALL define Pydantic models for Source, Document, and Chunk with the following fields:
- Source: id, canonical_domain, name (optional), rss_feed (optional)
- Document: id, source_id, canonical_url, title (optional), author (optional), published_at (optional), content_markdown
- Chunk: id, document_id, chunk_index, content_text

#### Scenario: Model validation
- **WHEN** a Source, Document, or Chunk is created with missing required fields
- **THEN** validation fails and the caller receives a clear error

### Requirement: SQLite persistence and schema
The core SHALL manage a SQLite schema with tables for sources, documents, and chunks, using slug-plus-hash identifiers as primary keys and enforcing uniqueness on canonical domain/URL values. Deletes MUST cascade from sources to documents to chunks.

#### Scenario: Cascading delete
- **WHEN** a Source is deleted
- **THEN** related Documents and Chunks are deleted automatically

### Requirement: FTS synchronization
The core SHALL create a `chunks_fts` FTS5 table with external content pointing to chunk plaintext and MUST maintain it with triggers on chunk insert, update, and delete.

#### Scenario: Chunk updates propagate to FTS
- **WHEN** a Chunk's plaintext content is updated
- **THEN** the corresponding FTS entry reflects the updated text

### Requirement: Vector storage
The core SHALL create a `chunks_vec` table using `sqlite-vec` with a 768-dimension vector and MUST keep it synchronized with chunk lifecycle operations.

#### Scenario: Chunk deletion removes vectors
- **WHEN** a Chunk is deleted
- **THEN** the associated vector row is removed

### Requirement: Source upsert behavior
The core SHALL upsert Sources by canonical domain: if a Source with the same canonical domain exists, the name and rss_feed fields MUST be updated instead of creating a new Source.

#### Scenario: Updating a Source by domain
- **WHEN** a Source upsert is performed with an existing canonical domain
- **THEN** the stored Source is updated and its id remains unchanged

### Requirement: Document upsert behavior
The core SHALL upsert Documents by canonical URL: if a Document with the same canonical URL exists, the metadata MUST be updated. If the markdown content changes, the system MUST delete existing Chunks and regenerate them.

#### Scenario: Document content changes
- **WHEN** a Document upsert supplies different markdown content for an existing canonical URL
- **THEN** previous Chunks are removed and new Chunks are created

### Requirement: Chunk generation
The core SHALL chunk Document content into plaintext segments with semantic boundaries, targeting ~2048 words per chunk and never exceeding ~8192 words. Each Chunk MUST store a chunk_index reflecting its order.

#### Scenario: Chunk indices are sequential
- **WHEN** a Document is chunked
- **THEN** chunks are stored with sequential chunk_index values starting at 0

### Requirement: Embedding generation
For each Chunk, the core MUST generate a 768-dimension embedding using `sentence-transformers` with the `nomic-embed-text-v1` model and persist it in the vector table.

#### Scenario: Embeddings stored per chunk
- **WHEN** a Chunk is created
- **THEN** a matching vector entry is stored with 768 dimensions

### Requirement: Hybrid search
The core SHALL provide a search interface that combines FTS ranking and vector cosine similarity with a weighted blend (default 0.7 FTS / 0.3 vector) and returns ranked results with associated Document and Chunk metadata.

#### Scenario: Search returns ranked results
- **WHEN** a user searches for a query string
- **THEN** results are ordered by the hybrid scoring algorithm
