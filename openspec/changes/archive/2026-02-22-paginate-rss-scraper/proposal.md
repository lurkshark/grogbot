## Why

Blogger and WordPress feeds can paginate beyond a single page, so the scraper currently misses older posts. We need a way to exhaust the feed (or cap it) to ensure consistent exports.

## What Changes

- Add pagination support for Blogger and WordPress RSS feeds to continue fetching pages until all posts are scraped or a maximum is reached.
- Introduce an optional CLI parameter to set a maximum post count, defaulting to 100.

## Capabilities

### New Capabilities
- _None_

### Modified Capabilities
- `rss-to-markdown-scraper`: Extend RSS feed ingestion to paginate Blogger/WordPress feeds and honor a configurable maximum post limit.

## Impact

- `@grogbot/goblin` RSS scraper CLI behavior and argument parsing.
- RSS feed ingestion and pagination logic for Blogger and WordPress.
