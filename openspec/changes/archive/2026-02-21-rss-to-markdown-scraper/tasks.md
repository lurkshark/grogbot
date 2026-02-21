## 1. Workspace and package setup

- [x] 1.1 Update monorepo and workspace naming to `grogbot`
- [x] 1.2 Replace placeholder `goblin` package with `@grogbot/goblin` package manifest
- [x] 1.3 Add CLI `bin` entry and TypeScript entry point wiring

## 2. RSS parsing and export core

- [x] 2.1 Add RSS parsing dependency and basic feed ingestion utility
- [x] 2.2 Implement item normalization (title/date/link/guid/content)
- [x] 2.3 Implement markdown writer with YAML frontmatter schema

## 3. CLI behavior and output

- [x] 3.1 Implement CLI command to accept feed URL and options
- [x] 3.2 Implement filename strategy and output directory handling
- [x] 3.3 Add overwrite/skip behavior with summary output

## 4. Compatibility validation

- [x] 4.1 Validate Blogger feed parsing against example feed
- [x] 4.2 Validate WordPress feed parsing against example feed

## 5. Documentation

- [x] 5.1 Document CLI usage and examples for RSS scraping
- [x] 5.2 Document frontmatter fields and output format
