# Grogbot

Grogbot is a uv-based Python monorepo for multiple systems. The first system, **search**, provides local storage and rank-fused search over markdown documents using FTS, vector, and link authority signals, exposed through a CLI and a server-rendered FastAPI app.

## Packages

- **`grogbot-search`** (`packages/search`): Core models, SQLite persistence, ingestion, chunking, embeddings, document-link graph storage, and three-signal rank-fused search.
- **`grogbot-cli`** (`packages/cli`): Typer-powered CLI (`grogbot`) that surfaces search functionality.
- **`grogbot-app`** (`packages/app`): FastAPI + Jinja browser app for the search system, with a landing page and server-rendered search UI.

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

## App Usage

The browser app lives in `grogbot_app.app:app`. It renders HTML directly from the same search database used by the CLI, so make sure you have already ingested content into your configured `db_path`.

Run it locally with uvicorn:

```bash
uv run --package grogbot-app uvicorn grogbot_app.app:app --reload
```

Then open `http://127.0.0.1:8000`.

Useful routes:

```bash
GET /
GET /search
GET /search/query?q=hello+world
```

Notes:

- `/` is a simple Grogbot landing page.
- `/search` shows the search form.
- `/search/query` renders up to 25 server-side search results for the `q` parameter.
- Static assets are served from `/assets`.
- There is no standalone JSON HTTP API in the active workspace.

## Document storage and embedding workflow

- `content_markdown` is accepted on upsert/ingest inputs, but it is **not persisted** in the `documents` table.
- Documents now persist a compact `content_hash` (6-character lowercase hex digest).
- URL and feed ingestion use a shared cleanup pipeline that aggressively removes scripts, widgets, unsafe links, malformed text noise, and other low-signal artifacts before chunk generation.
- Chunk generation is prose-oriented and hard-bounded: semantic grouping is preserved when possible, but fallback splitting ensures persisted chunks stay within strict safety limits for embedding.
- Outbound links are preserved from cleaned source content independently from prose pruning, so useful links can survive even when noisy text blocks are dropped.
- Upsert/ingestion regenerates plaintext chunks and outbound links when content changes.
- Re-ingest assumption: if chunking / cleanup behavior changes, rebuild the local corpus rather than expecting in-place migration of existing chunk rows.
- Embeddings are generated explicitly:
  - CLI: `grogbot search document embed <document_id>`
  - CLI (bulk): `grogbot search document embed-sync --maximum 100`
    - Shows a live progress bar with elapsed time and ETA on stderr while preserving the final JSON result on stdout.
- SearchService embedding API uses canonical methods only:
  - `embed_document_chunks(document_id)`
  - `synchronize_document_embeddings(maximum=...)`
    - Accepts an optional per-document progress callback so interactive callers can observe bulk embedding progress without moving CLI presentation logic into `grogbot-search`.
  - Legacy aliases `chunk_document` and `synchronize_document_chunks` have been removed.

## Development

Install workspace dependencies:

```bash
uv sync --extra test
```

Run package tests:

```bash
uv run --package grogbot-search --extra test pytest packages/search/tests
uv run --package grogbot-app --extra test pytest packages/app/tests
```

Run coverage checks for the search package with `pytest-cov`:

```bash
uv run --package grogbot-search --extra test \
  pytest packages/search/tests \
  --cov=grogbot_search --cov-report=term-missing
```

## Historical note

Archived OpenSpec artifacts may still reference the former `packages/search-core`, `packages/web`, and `packages/api` names. Those references describe the repository at the time those changes were authored and are not the current canonical package layout.
