## Why

Establish a uv-based monorepo foundation for grogbot and deliver the first system (search) with reusable core logic plus CLI and API surfaces. This enables consistent multi-system expansion while providing immediate value for storing and querying markdown documents.

## What Changes

- Create a uv workspace monorepo layout with separate packages for the search core library, Typer CLI, and FastAPI API.
- Implement the search core library with Pydantic models, SQLite persistence, FTS + vector search, chunking, and embeddings via `sentence-transformers` (`nomic-embed-text-v1`).
- Add orchestration workflows for creating documents from URLs and RSS feeds, including auto-creation of Sources.
- Build a Typer-based CLI (`grogbot`) with a `search` command group and subcommands that invoke search core functionality.
- Build a FastAPI app exposing the search system as HTTP endpoints that mirror the CLI capabilities.
- Add a shared configuration file at `~/.grogbot/config.toml` with env var override to control storage paths and related settings.

## Capabilities

### New Capabilities
- `monorepo-structure`: uv workspace structure with separate packages for search core, CLI, and API.
- `search-core`: Pydantic models plus SQLite-backed CRUD for Sources, Documents, and Chunks, including FTS + vector search and embeddings.
- `search-ingestion`: Orchestration to create documents from URLs and RSS feeds with canonicalization and auto Source management.
- `search-cli`: Typer CLI command surface for the search system, using config-based storage.
- `search-api`: FastAPI endpoints for the search system, using config-based storage.

### Modified Capabilities
- None.

## Impact

- New packages under a uv workspace; updated dependency graph for `typer`, `fastapi`, `sentence-transformers`, `python-readability`, RSS parsing, and `sqlite-vec`.
- New CLI entrypoint `grogbot` and new API service.
- SQLite schema additions (FTS + vector tables with triggers) and document ingestion workflows.
