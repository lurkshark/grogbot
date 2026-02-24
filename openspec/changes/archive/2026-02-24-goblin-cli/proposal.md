## Why

We need a repeatable CLI pipeline that turns RSS blog posts into structured, LLM-ready artifacts and stores them for search and retrieval. Building this now unlocks consistent extract/transform/load workflows and eliminates ad-hoc scripts.

## What Changes

- Add a new `@grogbot/goblin` CLI package under `packages/goblin/` (ESM) with a bin entry.
- Implement `extract`, `transform`, and `load` subcommands to support a full RSS → markdown → LLM transform → chunked load pipeline.
- Add shared utilities for slug/GUID generation, markdown frontmatter handling, and chunking.
- Introduce dependencies for RSS parsing, HTML readability, markdown conversion, Vercel AI SDK with OpenRouter, and Upstash Search.
- Add repo-level Prettier configuration and package-level TypeScript config inheriting from `tsconfig.base.json`.

## Capabilities

### New Capabilities
- `goblin-cli`: CLI tooling for RSS extract, LLM transform processing, and Upstash Search loading.

### Modified Capabilities
- 

## Impact

- New package under `packages/goblin/` with CLI bin.
- New runtime dependencies: RSS parser, `@mozilla/readability`, `turndown`, Vercel AI SDK + OpenRouter provider, Upstash Search client, and YAML/frontmatter tooling.
- Repository configuration additions for Prettier and TypeScript inheritance.
