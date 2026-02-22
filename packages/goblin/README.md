# @grogbot/goblin

CLI tool to scrape an RSS feed and export posts as markdown files with YAML frontmatter.

## Usage

```
goblin scrape <feed-url> [--out <dir>] [--overwrite] [--max-posts <n>]
```

### Options

- `--out`, `-o`: Output directory (defaults to current working directory).
- `--overwrite`: Overwrite existing files (default: skip existing).
- `--max-posts`, `-m`: Maximum number of posts to scrape (default: 100).

## Output format

Each RSS item becomes a markdown file with YAML frontmatter:

```
---
title: Post title
date: 2026-02-21T12:34:56.000Z
link: https://example.com/post
guid: https://example.com/post
author: Author Name
categories:
  - Category A
  - Category B
source: https://example.com/feed.xml
---

<post body>
```

### Frontmatter fields

- `title`: Title of the post.
- `date`: ISO 8601 timestamp (publication date or fallback).
- `link`: Canonical link to the post.
- `guid`: GUID or fallback identifier.
- `author`: Optional author value from the feed.
- `categories`: Optional category list.
- `source`: Feed URL.

## Testing

Offline integration tests use repository-local RSS fixtures and do not require network access.

```
pnpm --filter @grogbot/goblin test
```
