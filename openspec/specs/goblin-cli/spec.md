# goblin-cli

## Purpose

Provide the goblin CLI pipeline for RSS extraction, LLM transformation, and search loading.

## Requirements

### Requirement: CLI exposes goblin subcommands

The system SHALL provide a `goblin` CLI with `extract`, `transform`, and `load` subcommands and their required arguments.

#### Scenario: User inspects CLI usage
- **WHEN** the user runs `goblin --help`
- **THEN** the CLI displays usage including `extract`, `transform`, and `load` with their required arguments

### Requirement: Extract writes normalized markdown files

The `extract` subcommand SHALL read a staging directory and RSS feed URL, then write one markdown file per valid feed item into `staging-directory/ingest/`.

#### Scenario: Extract persists items to staging directory
- **WHEN** the user runs `goblin extract <staging-directory> <feed-url>` with a feed containing valid items
- **THEN** the CLI writes one markdown file per valid item in `staging-directory/ingest/`

### Requirement: Extract content sources and filtering

The extract pipeline SHALL prefer RSS content fields when present; otherwise it SHALL fetch the article URL, parse it with `@mozilla/readability`, and convert to markdown using `turndown`. Items missing title or publish date SHALL be skipped and summarized at the end of the run.

#### Scenario: Extract skips missing metadata
- **WHEN** the feed contains items without a title or publish date
- **THEN** those items are skipped and reported in a summary after processing completes

### Requirement: Extract metadata, slug, and GUID

Each extracted markdown file SHALL include YAML frontmatter with `guid`, `slug`, `title`, `date`, and `url`. The slug SHALL be `YYYY-MM-DD--title-slug`, and the GUID SHALL be a stable SHA-256 hash of the slug. The filename SHALL be the slug with a `.md` extension.

#### Scenario: Extract file naming and frontmatter
- **WHEN** an item with title and publish date is extracted
- **THEN** the output filename and frontmatter slug follow `YYYY-MM-DD--title-slug` and the GUID is the SHA-256 hash of that slug

### Requirement: Transform processes ingest files with LLM

The `transform` subcommand SHALL read all markdown files in `staging-directory/ingest/`, apply the provided prompt via the Vercel AI SDK Global Provider configured for OpenRouter, and write outputs to `staging-directory/<namespace>/`. It SHALL support an optional model override and default to Gemini 3 Flash when not provided. Processing SHALL run with a maximum concurrency of 8 and overwrite existing transform files.

#### Scenario: Transform writes namespace outputs
- **WHEN** the user runs `goblin transform <staging-directory> <namespace> <prompt>`
- **THEN** the CLI writes a markdown transform for each ingest file into `staging-directory/<namespace>/` using OpenRouter with max concurrency 8

### Requirement: Transform metadata, slug, GUID, and extract info

Each transform markdown file SHALL include YAML frontmatter with `guid`, `slug`, `source_guid`, and `source_slug`. The transform slug SHALL be the extract slug plus the namespace (joined as `extractSlug--namespace`), and the GUID SHALL be a SHA-256 hash of the transform slug. The CLI SHALL also write `staging-directory/<namespace>-extract-info.yaml` containing the prompt and model metadata for the run.

#### Scenario: Transform writes metadata and info file
- **WHEN** transform outputs are generated for a namespace
- **THEN** each output includes frontmatter with transform and source identifiers and the staging directory root contains `<namespace>-extract-info.yaml`

### Requirement: Load chunks and writes to Upstash Search

The `load` subcommand SHALL read markdown files from `staging-directory/<namespace>/` (or `staging-directory/ingest/` when namespace is omitted), exclude frontmatter from content, and chunk the markdown into sections of maximum size (default 1500 characters) with ~10% overlap while retaining headings at chunk boundaries. Each chunk SHALL be written to the Upstash Search index named by the namespace (or `ingest`) with metadata fields `chunk_index` and `source_guid`.

#### Scenario: Load indexes chunked content
- **WHEN** the user runs `goblin load <staging-directory>` with default options
- **THEN** the CLI indexes chunked content from `staging-directory/ingest/` into the `ingest` index with chunk metadata and heading-preserved boundaries

### Requirement: Load uses standard Upstash Search environment variables

The load pipeline SHALL authenticate to Upstash Search using `UPSTASH_SEARCH_REST_URL` and `UPSTASH_SEARCH_REST_TOKEN` environment variables.

#### Scenario: Load authenticates with Upstash environment variables
- **WHEN** the user runs `goblin load` with the required environment variables set
- **THEN** the CLI uses those values to connect to Upstash Search
