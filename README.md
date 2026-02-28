# Grogbot

Grogbot is a uv-based Python monorepo for multiple systems. The first system, **search**, provides local storage and rank-fused search over markdown documents, exposed through both a CLI and a FastAPI service.

## Packages

- **`grogbot-search-core`** (`packages/search-core`): Core models, SQLite persistence, ingestion, chunking, embeddings, and rank-fused search.
- **`grogbot-cli`** (`packages/cli`): Typer-powered CLI (`grogbot`) that surfaces search functionality.
- **`grogbot-api`** (`packages/api`): FastAPI app exposing the search system over HTTP.

## Configuration

Grogbot reads configuration from `~/.grogbot/config.toml` by default. Override with `GROGBOT_CONFIG`.

```toml
[search]
db_path = "~/.grogbot/search.db"
```

## CLI Usage

```bash
grogbot search source upsert example.com --name "Example"
grogbot search ingest-url https://example.com/article

# Run a rank-fused query
grogbot search query "hello world" --limit 5
```

## API Usage

The FastAPI app lives in `grogbot_api.app:app` and exposes `/search` routes.

Examples:

```bash
GET /search/sources
POST /search/sources
GET /search/documents/{document_id}
POST /search/ingest/url
GET /search/query?q=hello+world
```

## Development

Install test dependencies for the search core and run pytest:

```bash
uv sync --extra test
uv run pytest packages/search-core/tests
```
