## Context

Grogbot is currently an empty repository and needs a uv-based monorepo structure that can host multiple systems. The first system (search) must manage Sources, Documents, and Chunks in SQLite, expose CRUD + orchestration workflows, and surface capabilities through a Typer CLI and a FastAPI service. Search must combine FTS and vector similarity (sqlite-vec) with embeddings generated locally via `sentence-transformers` using the `nomic-embed-text-v1` model. Configuration is file-based at `~/.grogbot/config.toml` with an env var override.

## Goals / Non-Goals

**Goals:**
- Establish a uv workspace with discrete packages: search core, CLI, API.
- Implement SQLite persistence for Sources, Documents, and Chunks with cascading deletes and synchronization triggers for FTS/vec tables.
- Provide orchestration for ingesting documents from URLs and RSS feeds, including automatic Source creation and canonical URL/domain handling.
- Expose search functionality in a CLI and a FastAPI service that share the same core logic and configuration.
- Provide hybrid search scoring (FTS + vector) with a simple weighted blend.

**Non-Goals:**
- Production-grade distributed search infrastructure or cloud storage.
- Multi-user authentication/authorization.
- Advanced ranking, personalization, or multilingual embeddings beyond `nomic-embed-text-v1`.

## Decisions

- **Monorepo layout**: Use a uv workspace with top-level `pyproject.toml` and separate packages for `search-core`, `cli`, and `api` to keep platform logic isolated from core functionality.
  - *Alternatives considered*: Single package with optional extras (rejected to keep separation of concerns and packaging clarity).

- **Persistence**: Use SQLite for local storage with `fts5` for full-text search and `sqlite-vec` for 768-dim embeddings. FTS will use an external content table pointing at chunk plaintext, with triggers for insert/update/delete.
  - *Alternatives considered*: Postgres + pgvector (rejected due to local-first goal and CLI simplicity).

- **Identifiers**: Store canonical domain (Sources) and canonical URL (Documents) with unique constraints, but use a human-friendly slug plus 6-char hash as the primary key for CLI/API ergonomics.
  - *Alternatives considered*: Pure UUIDs (rejected as less friendly for CLI), natural keys (rejected to avoid long identifiers in URLs/CLI).

- **Chunking heuristic**: Chunk markdown-derived plaintext by heading sections, then paragraphs, merging small segments toward ~2048 words and enforcing a max of ~8192 words by sentence splitting. Semantic completeness prioritized over exact sizing.
  - *Alternatives considered*: Fixed-size token windows (rejected to preserve readability and avoid tokenizer dependency).

- **Embeddings**: Use `sentence-transformers` with `nomic-embed-text-v1` for local embeddings and cosine similarity for vector ranking.
  - *Alternatives considered*: Hosted embeddings (rejected to avoid external dependency).

- **Ingestion pipeline**: For URL ingestion, fetch HTML, use `python-readability` to extract main content, then convert to markdown (e.g., `markdownify`). For RSS ingestion, parse feeds (e.g., `feedparser`), convert `content:encoded` HTML to markdown, and infer metadata from entries. Auto-create Sources based on canonical domain if missing.
  - *Alternatives considered*: Custom scraping rules (rejected for initial scope).

- **Config resolution**: Default config at `~/.grogbot/config.toml`, overridden by an env var (e.g., `GROGBOT_CONFIG`). Both CLI and API resolve config the same way for shared storage settings.
  - *Alternatives considered*: Per-package config files (rejected to keep a single source of truth).

- **Hybrid search scoring**: Combine FTS rank and cosine similarity with a weighted blend (default 0.7 FTS / 0.3 vector) and return ranked results through core interfaces.
  - *Alternatives considered*: Vector-only search (rejected to preserve keyword precision).

## Risks / Trade-offs

- **Local model size / startup time** → Cache the `SentenceTransformer` instance and load lazily.
- **Chunk sizing heuristic may be imprecise** → Provide deterministic chunking with semantic splits and guardrails on min/max lengths.
- **sqlite-vec availability** → Add installation guidance and validate extension loading at startup with clear errors.
- **Feed/HTML parsing variability** → Keep ingestion resilient with best-effort parsing and store partial metadata when unavailable.

## Open Questions

- Finalize the environment variable name for config override (default to `GROGBOT_CONFIG` unless overridden).
