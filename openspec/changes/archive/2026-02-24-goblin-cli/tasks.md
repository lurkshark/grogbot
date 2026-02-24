## 1. Package setup and tooling

- [x] 1.1 Scaffold `packages/goblin/` with `package.json`, ESM settings, bin entry, and `src/` layout
- [x] 1.2 Add `tsconfig.json` in `packages/goblin/` extending `tsconfig.base.json`
- [x] 1.3 Add Prettier configuration and formatting scripts at the repo root
- [x] 1.4 Add required runtime dependencies and workspace configuration updates

## 2. Shared utilities

- [x] 2.1 Implement slug and GUID helpers (date/title slugging, SHA-256 hashing)
- [x] 2.2 Implement frontmatter read/write helpers for markdown files
- [x] 2.3 Implement RSS item normalization and HTML-to-markdown conversion helpers
- [x] 2.4 Implement markdown chunking utility with heading-aware boundaries and overlap

## 3. Extract command

- [x] 3.1 Implement RSS feed parsing and item filtering (skip missing title/date)
- [x] 3.2 Write extract markdown files with frontmatter into `pond/ingest/`
- [x] 3.3 Add end-of-run summary for skipped items

## 4. Transform command

- [x] 4.1 Configure Vercel AI SDK Global Provider with OpenRouter and default model
- [x] 4.2 Implement concurrency-limited transform processing over extract files
- [x] 4.3 Write transform markdown outputs with metadata and `<namespace>-extract-info.yaml`

## 5. Load command

- [x] 5.1 Implement namespace resolution and markdown loading for load inputs
- [x] 5.2 Chunk markdown content (excluding frontmatter) and attach chunk metadata
- [x] 5.3 Push chunks to Upstash Search using standard environment variables

## 6. CLI wiring and docs

- [x] 6.1 Wire CLI commands/arguments and help text for extract/transform/load
- [x] 6.2 Add basic usage notes to package README
