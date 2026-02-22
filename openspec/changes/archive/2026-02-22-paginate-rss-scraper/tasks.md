## 1. CLI Options

- [x] 1.1 Locate the RSS scraper CLI entrypoint and add a `--max-posts` option (default 100) to argument parsing
- [x] 1.2 Wire the parsed max-posts value into the RSS ingestion pipeline (including fixtures)

## 2. Pagination Logic

- [x] 2.1 Identify Blogger feed pagination link format and implement next-page discovery
- [x] 2.2 Identify WordPress feed pagination link format and implement next-page discovery
- [x] 2.3 Add pagination loop with total post counter and stop when max reached or no next page

## 3. Tests & Fixtures

- [x] 3.1 Update/add fixture RSS files representing multi-page Blogger and WordPress feeds
- [x] 3.2 Add or update tests to verify pagination stops at max posts and at end of feed
