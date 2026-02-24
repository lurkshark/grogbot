# goblin-cli

## Purpose

Provide the goblin CLI pipeline for RSS ingest, LLM extraction, and search storage.

## Requirements

### Requirement: CLI exposes goblin subcommands

The system SHALL provide a `goblin` CLI with `ingest`, `extract`, and `store` subcommands and their required arguments.

#### Scenario: User inspects CLI usage
- **WHEN** the user runs `goblin --help`
- **THEN** the CLI displays usage including `ingest`, `extract`, and `store` with their required arguments

### Requirement: Ingest writes normalized markdown files

The `ingest` subcommand SHALL read a pond directory and RSS feed URL, then write one markdown file per valid feed item into `pond/ingest/`.

#### Scenario: Ingest persists items to pond
- **WHEN** the user runs `goblin ingest <pond> <feed-url>` with a feed containing valid items
- **THEN** the CLI writes one markdown file per valid item in `pond/ingest/`

### Requirement: Ingest content sources and filtering

The ingest pipeline SHALL prefer RSS content fields when present; otherwise it SHALL fetch the article URL, parse it with `@mozilla/readability`, and convert to markdown using `turndown`. Items missing title or publish date SHALL be skipped and summarized at the end of the run.

#### Scenario: Ingest skips missing metadata
- **WHEN** the feed contains items without a title or publish date
- **THEN** those items are skipped and reported in a summary after processing completes

### Requirement: Ingest metadata, slug, and GUID

Each ingest markdown file SHALL include YAML frontmatter with `guid`, `slug`, `title`, `date`, and `url`. The slug SHALL be `YYYY-MM-DD--title-slug`, and the GUID SHALL be a stable SHA-256 hash of the slug. The filename SHALL be the slug with a `.md` extension.

#### Scenario: Ingest file naming and frontmatter
- **WHEN** an item with title and publish date is ingested
- **THEN** the output filename and frontmatter slug follow `YYYY-MM-DD--title-slug` and the GUID is the SHA-256 hash of that slug

### Requirement: Extract processes ingest files with LLM

The `extract` subcommand SHALL read all markdown files in `pond/ingest/`, apply the provided prompt via the Vercel AI SDK Global Provider configured for OpenRouter, and write outputs to `pond/<namespace>/`. It SHALL support an optional model override and default to Gemini 3 Flash when not provided. Processing SHALL run with a maximum concurrency of 8 and overwrite existing extract files.

#### Scenario: Extract writes namespace outputs
- **WHEN** the user runs `goblin extract <pond> <namespace> <prompt>`
- **THEN** the CLI writes a markdown extract for each ingest file into `pond/<namespace>/` using OpenRouter with max concurrency 8

### Requirement: Extract metadata, slug, GUID, and extract info

Each extract markdown file SHALL include YAML frontmatter with `guid`, `slug`, `source_guid`, and `source_slug`. The extract slug SHALL be the ingest slug plus the namespace (joined as `ingestSlug--namespace`), and the GUID SHALL be a SHA-256 hash of the extract slug. The CLI SHALL also write `pond/<namespace>-extract-info.yaml` containing the prompt and model metadata for the run.

#### Scenario: Extract writes metadata and info file
- **WHEN** extract outputs are generated for a namespace
- **THEN** each output includes frontmatter with extract and source identifiers and the pond root contains `<namespace>-extract-info.yaml`

### Requirement: Store chunks and writes to Upstash Search

The `store` subcommand SHALL read markdown files from `pond/<namespace>/` (or `pond/ingest/` when namespace is omitted), exclude frontmatter from content, and chunk the markdown into sections of maximum size (default 1500 characters) with ~10% overlap while retaining headings at chunk boundaries. Each chunk SHALL be written to the Upstash Search index named by the namespace (or `ingest`) with metadata fields `chunk_index` and `source_guid`.

#### Scenario: Store indexes chunked content
- **WHEN** the user runs `goblin store <pond>` with default options
- **THEN** the CLI indexes chunked content from `pond/ingest/` into the `ingest` index with chunk metadata and heading-preserved boundaries

### Requirement: Store uses standard Upstash Search environment variables

The store pipeline SHALL authenticate to Upstash Search using `UPSTASH_SEARCH_REST_URL` and `UPSTASH_SEARCH_REST_TOKEN` environment variables.

#### Scenario: Store authenticates with Upstash environment variables
- **WHEN** the user runs `goblin store` with the required environment variables set
- **THEN** the CLI uses those values to connect to Upstash Search
