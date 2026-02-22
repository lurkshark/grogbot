## Context

The `@grogbot/goblin` scraper currently ingests a single RSS feed URL and exports the posts it finds, supporting Blogger and WordPress. Blogger and WordPress feeds can paginate, so a single feed page can omit older posts. We need to paginate until all posts are collected or a configurable maximum is reached, while preserving the existing offline fixture support.

## Goals / Non-Goals

**Goals:**
- Add pagination for Blogger and WordPress feed ingestion.
- Introduce an optional CLI parameter to cap the total number of posts scraped, defaulting to 100.
- Stop pagination when the maximum is reached or when the feed ends.

**Non-Goals:**
- Adding pagination for non-Blogger/WordPress RSS feeds.
- Changing the export format or frontmatter schema.
- Introducing new storage or caching mechanisms.

## Decisions

- **CLI flag naming**: Add an optional `--max-posts` (alias `-m` if supported) numeric parameter with a default of `100`, parsed alongside existing CLI options.
  - *Alternative*: Use a config file or environment variable. Rejected to keep parity with current CLI usage.
- **Pagination strategy**: For Blogger and WordPress, detect and follow the next/older page link in the feed until no further page exists or the max post cap is reached.
  - *Alternative*: Attempt to request a large page size via query parameters. Rejected because Blogger/WordPress behavior varies and pagination is already exposed in feed links.
- **Termination condition**: Track total posts exported and halt fetching when `total >= maxPosts`, even if more pages are available.
  - *Alternative*: Fetch all pages then truncate. Rejected to avoid unnecessary network requests.
- **Fixture support**: For repository-local fixtures, allow pagination to read from additional fixture files when they exist; otherwise treat the single fixture as end-of-feed.
  - *Alternative*: Disable pagination for fixtures. Rejected to keep behavior consistent across offline/online runs.

## Risks / Trade-offs

- **Risk**: Feed pagination link formats differ between Blogger and WordPress. → *Mitigation*: Encapsulate pagination parsing per platform, add tests for representative fixtures.
- **Risk**: Large feeds could cause long runtimes. → *Mitigation*: Default max of 100 posts and stop early when cap is reached.
- **Trade-off**: Additional logic in feed ingestion may increase complexity. → *Mitigation*: Keep pagination logic isolated to the feed-specific parser modules.
