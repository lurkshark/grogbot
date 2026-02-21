## Context

The repository currently includes a placeholder `goblin` package. We need to evolve this into a real workspace package named `@grogbot/goblin` that provides a CLI to ingest RSS feeds and emit markdown files with YAML frontmatter. This introduces a new CLI surface, parsing dependencies, and filesystem output conventions.

## Goals / Non-Goals

**Goals:**
- Provide a CLI entry point in `@grogbot/goblin` that accepts an RSS feed URL.
- Parse feed items into markdown files with deterministic filenames and YAML frontmatter metadata.
- Establish clear output behavior (target directory, overwrite strategy, metadata fields).

**Non-Goals:**
- Building a full content management system or rich HTML-to-Markdown conversion beyond basic needs.
- Supporting non-RSS feed formats unless easily handled by the chosen parser.
- Implementing publishing or syncing back to a blog platform.

## Decisions

- **CLI shape and options**: Provide a single command (e.g., `goblin scrape <feed-url>`) with options for output directory, filename strategy, and overwrite behavior. This keeps the initial interface small while allowing deterministic output paths for automation.
  - Alternatives: multiple subcommands for feed discovery, item listing, and export. Rejected to keep the first iteration focused.

- **RSS parsing dependency**: Use a mature RSS/Atom parsing library that normalizes item fields (title, link, pubDate, content). This reduces custom parsing logic and supports common feed variants.
  - Alternatives: implement a custom RSS parser. Rejected due to higher maintenance and edge cases.

- **Markdown generation**: Store raw content as markdown if already in markdown; otherwise, perform minimal HTML-to-Markdown conversion. This avoids losing content while keeping output usable in markdown-based workflows.
  - Alternatives: store raw HTML in markdown body. Rejected because it reduces readability for markdown consumers.

- **Frontmatter schema**: Use YAML frontmatter with fields such as `title`, `date`, `link`, `author`, `guid`, `categories`, and `source`. This provides predictable metadata for downstream tooling.
  - Alternatives: JSON frontmatter or custom metadata blocks. Rejected to align with common markdown tooling.

- **Filename strategy**: Default to a slug derived from title plus publication date (e.g., `2026-02-21-post-title.md`) with a GUID fallback when title is missing. This yields stable, human-friendly filenames and avoids collisions.
  - Alternatives: use GUID-only filenames. Rejected because it is less readable.

## Risks / Trade-offs

- [Feeds with inconsistent metadata] → Mitigation: implement fallbacks (title from link, date from updated fields, GUID from link).
- [HTML conversion quality] → Mitigation: start with minimal conversion and document limitations; allow future enhancement.
- [File overwrites or duplicates] → Mitigation: provide `--overwrite` and default to skip existing files with a summary report.
- [Large feeds] → Mitigation: support a `--limit` option or pagination if the parser exposes it.

## Migration Plan

- Rename or replace the placeholder `goblin` package with `@grogbot/goblin` in the workspace.
- Introduce the CLI entry point and ensure it is wired to the package `bin` field.
- Add RSS parsing and markdown/frontmatter generation dependencies.
- Document CLI usage and update any references to the placeholder package.
- Rollback: revert to placeholder package and remove new dependencies if needed.

## Open Questions

- What is the exact CLI command name and expected flags (`--out`, `--overwrite`, `--limit`)?
- What is the desired default output directory (current working dir vs a configured path)?
- Should we support content extraction from `content:encoded` vs `description` when both exist?
