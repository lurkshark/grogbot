## Why

We need a real CLI tool in the `@grogbot/goblin` package to turn RSS blog feeds into markdown files with YAML frontmatter. This replaces the current placeholder package with a usable workflow for content ingestion.

## What Changes

- Define the monorepo identity as `grogbot` and the workspace package name as `@grogbot/goblin`.
- Implement a CLI tool that accepts an RSS feed URL, parses posts, and writes each post to a markdown file with YAML frontmatter metadata.
- Establish the expected input/output behavior and metadata fields for the scraper.

## Capabilities

### New Capabilities
- `rss-to-markdown-scraper`: CLI tool behavior for ingesting an RSS feed and emitting markdown files with YAML frontmatter per post.

### Modified Capabilities
- `goblin-package-placeholder`: Replace the placeholder package requirements with the real `@grogbot/goblin` package and CLI entry point requirements.

## Impact

- `packages/@grogbot/goblin` package structure, CLI entry point, and build output.
- Workspace package naming and any references to the placeholder `goblin` package.
- Dependencies for RSS parsing and markdown/frontmatter generation.
