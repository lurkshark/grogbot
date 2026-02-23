# @grogbot/alchemist

CLI tool to ingest markdown files, generate embeddings, and persist vectors plus content to a local LanceDB database.

## Usage

```
alchemist ingest <dir> [--model <name>]
```

### Options

- `--model`, `-m`: HuggingFace embedding model name (default: `Xenova/all-MiniLM-L6-v2`).

## Behavior

- Discovers `.md` files in the provided directory.
- Generates embeddings for each file using LangChainJS HuggingFace transformers embeddings.
- Stores vectors and post content in a local LanceDB database located at `./lancedb` (relative to the current working directory).
- Reuses the existing database on subsequent runs.

## Output summary

On completion, the CLI logs an ingestion summary like:

```
Ingested 12 markdown files into LanceDB at /path/to/project/lancedb.
```

## Testing

Integration tests run offline using mocked embeddings/vector store.

```
pnpm --filter @grogbot/alchemist test
```
