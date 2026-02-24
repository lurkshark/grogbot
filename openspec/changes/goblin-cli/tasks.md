## 1. Package setup and tooling

- [ ] 1.1 Scaffold `packages/goblin/` with `package.json`, ESM settings, bin entry, and `src/` layout
- [ ] 1.2 Add `tsconfig.json` in `packages/goblin/` extending `tsconfig.base.json`
- [ ] 1.3 Add Prettier configuration and formatting scripts at the repo root
- [ ] 1.4 Add required runtime dependencies and workspace configuration updates

## 2. Shared utilities

- [ ] 2.1 Implement slug and GUID helpers (date/title slugging, SHA-256 hashing)
- [ ] 2.2 Implement frontmatter read/write helpers for markdown files
- [ ] 2.3 Implement RSS item normalization and HTML-to-markdown conversion helpers
- [ ] 2.4 Implement markdown chunking utility with heading-aware boundaries and overlap

## 3. Ingest command

- [ ] 3.1 Implement RSS feed parsing and item filtering (skip missing title/date)
- [ ] 3.2 Write ingest markdown files with frontmatter into `pond/ingest/`
- [ ] 3.3 Add end-of-run summary for skipped items

## 4. Extract command

- [ ] 4.1 Configure Vercel AI SDK Global Provider with OpenRouter and default model
- [ ] 4.2 Implement concurrency-limited extract processing over ingest files
- [ ] 4.3 Write extract markdown outputs with metadata and `<namespace>-extract-info.yaml`

## 5. Store command

- [ ] 5.1 Implement namespace resolution and markdown loading for store inputs
- [ ] 5.2 Chunk markdown content (excluding frontmatter) and attach chunk metadata
- [ ] 5.3 Push chunks to Upstash Search using standard environment variables

## 6. CLI wiring and docs

- [ ] 6.1 Wire CLI commands/arguments and help text for ingest/extract/store
- [ ] 6.2 Add basic usage notes to package README
