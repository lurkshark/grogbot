## Context

We are introducing a new CLI package to handle a multi-stage pipeline: ingest RSS feeds into normalized markdown, extract LLM-processed outputs into namespaces, and store chunked content in Upstash Search. The repo currently has no packages or tooling, so this change sets up the package, CLI entrypoint, and shared utilities. The solution must use the Vercel AI SDK (Global Provider) with OpenRouter, and produce stable slugs and GUIDs for each artifact.

## Goals / Non-Goals

**Goals:**
- Provide an ESM CLI at `packages/goblin/` with `ingest`, `extract`, and `store` subcommands.
- Implement a stable pond directory layout and metadata conventions for ingest and extract outputs.
- Use RSS content directly when available and fall back to HTML readability + markdown conversion.
- Run LLM extraction via OpenRouter with controlled concurrency.
- Chunk markdown content with heading-aware boundaries and ~10% overlap, then store in Upstash Search.
- Establish formatting (Prettier) and TypeScript config inheritance from `tsconfig.base.json`.

**Non-Goals:**
- Building a UI or server-side service for the pipeline.
- Long-term scheduling or daemonized ingestion.
- Complex data models beyond markdown + frontmatter.

## Decisions

- **Package structure & CLI framework**: Create `packages/goblin/` with an ESM entrypoint and CLI bin. Use a lightweight CLI framework (e.g., `commander`) to define subcommands and arguments consistently across ingest/extract/store.
  - **Alternatives considered**: Raw `process.argv` parsing (less ergonomic), `yargs` (heavier API surface).

- **Pond layout & filenames**: Write ingest outputs to `pond/ingest/`. Extract outputs are written to `pond/<namespace>/`, using a stable slug `ingestSlug + "--" + namespace` as the filename stem. GUIDs are SHA-256 hashes of the slug. Frontmatter is stored in each markdown file; the main body is markdown.
  - **Alternatives considered**: Using UUIDs for filenames (not stable), single shared directory (ambiguous provenance).

- **RSS ingestion & markdown conversion**: Prefer RSS `content`/`content:encoded` when present. Otherwise fetch the article URL, parse with `@mozilla/readability` (via JSDOM), and convert to markdown with `turndown`.
  - **Alternatives considered**: Always fetching content (slower, more fragile), using only RSS description fields (lossy).

- **LLM extraction via OpenRouter**: Use Vercel AI SDK Global Provider with the OpenRouter provider. Default model is Gemini 3 Flash when not provided on the CLI. Use a concurrency limit of 8 (e.g., `p-limit`) and overwrite existing extract files. Store prompt/model metadata in `pond/<namespace>-extract-info.yaml` (YAML) rather than frontmatter.
  - **Alternatives considered**: Per-call provider configuration (more boilerplate), storing prompt/model in frontmatter (noisy, repeats per file).

- **Chunking strategy for store**: Parse markdown to preserve heading boundaries. Treat headings + following content as blocks, build chunks up to a max size (default 1500 chars). If a block is larger than max, split by paragraph. Add ~10% overlap by prefixing the next chunk with the trailing portion of the previous chunk, while ensuring headings are repeated at boundaries when a section spans chunks.
  - **Alternatives considered**: Simple character slicing (breaks structure), no overlap (hurts semantic continuity).

- **Search storage**: Use Upstash Search with standard environment variables (`UPSTASH_SEARCH_REST_URL`, `UPSTASH_SEARCH_REST_TOKEN`). Index name is the namespace or `ingest` when omitted. Store chunk content plus metadata fields `chunk_index` and `source_guid`.
  - **Alternatives considered**: Separate metadata store (adds complexity), storing the entire frontmatter as part of the chunk content (pollutes embeddings).

## Risks / Trade-offs

- **HTML fetching variability** → Mitigation: fall back on RSS content when available and log failures with skipped item report.
- **LLM throughput/limits** → Mitigation: concurrency cap at 8 and allow optional model override.
- **Chunking accuracy** → Mitigation: use a markdown parser to preserve heading boundaries and test with varied content.
