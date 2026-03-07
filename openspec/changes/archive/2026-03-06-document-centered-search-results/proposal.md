## Why

The current search behavior is chunk-centered: multiple results can point to the same document when several chunks from that document rank highly. This makes the search response harder to consume in the CLI and API because callers want a ranked list of documents, each with a single representative snippet.

## What Changes

- Change search result semantics from chunk-centered ranking output to document-centered ranking output.
- Return each matching document at most once, using its highest-ranked chunk as the representative snippet in the response.
- Apply the `limit` parameter to unique documents instead of raw chunk rows.
- Preserve the existing response shape so each result still includes both a `document` and its representative `chunk`.

## Capabilities

### New Capabilities
- `document-centered-search`: Search returns unique documents ranked by hybrid search score, with one representative chunk per document.

### Modified Capabilities
- None.

## Impact

- Affects `packages/search-core/src/grogbot_search/service.py` search query and result assembly.
- Affects search behavior observed through `packages/cli/src/grogbot_cli/app.py` and `packages/api/src/grogbot_api/app.py`.
- Affects tests in `packages/search-core/tests/test_service.py` to validate unique-document results and document-based limit semantics.
