## 1. Workspace and packaging

- [ ] 1.1 Create the root uv workspace `pyproject.toml` and register member packages under `packages/`
- [ ] 1.2 Scaffold `packages/search-core`, `packages/cli`, and `packages/api` with src layouts and package metadata
- [ ] 1.3 Configure package dependencies so CLI/API depend on search-core and define the `grogbot` CLI entrypoint

## 2. Configuration

- [ ] 2.1 Implement a shared config loader with default `~/.grogbot/config.toml` and `GROGBOT_CONFIG` override
- [ ] 2.2 Add config settings for the search database path (default `~/.grogbot/search.db`) and ensure directories are created

## 3. Search core persistence and models

- [ ] 3.1 Implement Pydantic models for Source, Document, and Chunk plus slug/hash helpers
- [ ] 3.2 Implement SQLite schema creation for sources, documents, chunks, `chunks_fts`, and `chunks_vec` with triggers
- [ ] 3.3 Build CRUD/upsert operations for Sources and Documents, including cascade deletes and chunk regeneration
- [ ] 3.4 Implement chunking logic with semantic splits and chunk_index sequencing
- [ ] 3.5 Implement embedding generation with `sentence-transformers` and vector persistence
- [ ] 3.6 Implement hybrid search queries combining FTS and vector similarity

## 4. Search ingestion workflows

- [ ] 4.1 Implement `createDocumentFromURL` (fetch, readability, markdown conversion, metadata extraction)
- [ ] 4.2 Implement `createDocumentsFromFeed` using RSS/Atom parsing and canonical URL handling
- [ ] 4.3 Wire ingestion to auto-create Sources and upsert Documents with chunk/embedding updates

## 5. CLI surface

- [ ] 5.1 Implement Typer `grogbot` app with `search` group and subcommands for source/document CRUD
- [ ] 5.2 Add CLI commands for URL/feed ingestion and hybrid query
- [ ] 5.3 Wire CLI outputs to JSON responses using core models

## 6. API surface

- [ ] 6.1 Implement FastAPI app with `/search` routes for sources, documents, ingestion, and query
- [ ] 6.2 Wire API handlers to the core library with config-based storage
