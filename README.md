# Grogbot

Grogbot is a uv-based Python monorepo for multiple systems. The first system, **search**, provides local storage and rank-fused search over markdown documents using FTS, vector, and link authority signals, exposed through both a CLI and a FastAPI service.

## Packages

- **`grogbot-search-core`** (`packages/search-core`): Core models, SQLite persistence, ingestion, chunking, embeddings, document-link graph storage, and three-signal rank-fused search.
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
POST /search/documents/embed
POST /search/documents/embed/sync
GET /search/query?q=hello+world
```

## Document storage and embedding workflow

- `content_markdown` is accepted on upsert/ingest inputs, but it is **not persisted** in the `documents` table.
- Documents now persist a compact `content_hash` (6-character lowercase hex digest).
- Upsert/ingestion regenerates plaintext chunks and outbound links when content changes.
- Embeddings are generated explicitly:
  - CLI: `grogbot search document embed <document_id>`
  - CLI (bulk): `grogbot search document embed-sync --maximum 100`
  - API: `POST /search/documents/embed`
  - API (bulk): `POST /search/documents/embed/sync`
- SearchService embedding API uses canonical methods only:
  - `embed_document_chunks(document_id)`
  - `synchronize_document_embeddings(maximum=...)`
  - Legacy aliases `chunk_document` and `synchronize_document_chunks` have been removed.

## Development

Install test dependencies for the search core and run pytest:

```bash
uv sync --extra test
uv run pytest packages/search-core/tests
```

Run coverage checks with `pytest-cov`:

```bash
uv run --package grogbot-search-core --extra test \
  pytest packages/search-core/tests \
  --cov=grogbot_search --cov-report=term-missing
```
