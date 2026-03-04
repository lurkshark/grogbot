## 1. Search-core pagination support

- [x] 1.1 Extend `create_documents_from_feed` with `paginate: bool = False` and implement rel="next" pagination with url resolution, loop detection, 100-page cap, and best-effort stop on page failures
- [x] 1.2 Extend `create_documents_from_opml` with `paginate: bool = False` and pass the flag through to feed ingestion

## 2. API and CLI surface updates

- [x] 2.1 Add `paginate: bool = False` to the feed ingest API request model and pass it through to the service call
- [x] 2.2 Add a `--paginate` option to the CLI `ingest-feed` command and pass it through to the service call
- [x] 2.3 Update CLI bootstrap feed ingestion to call `create_documents_from_feed(..., paginate=True)`

## 3. Test coverage

- [x] 3.1 Add paginated feed fixtures in the test HTTP server (next link + second page)
- [x] 3.2 Add tests for `create_documents_from_feed` pagination (default false vs true, 100-page/loop stop if feasible)
- [x] 3.3 Add a best-effort pagination test that stops when a subsequent page fails
