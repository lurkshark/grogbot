## Why

The RSS-to-markdown package lacks tests that exercise its full input-to-output flow, which risks regressions in feed parsing and Markdown formatting. Adding offline integration-style tests now will improve confidence without requiring network access or external file permissions.

## What Changes

- Add offline integration-style tests that execute the RSS-to-markdown workflow against local fixtures.
- Ensure tests run without internet access and only use files within the repository.
- Cover representative feed variants (e.g., typical RSS items, missing fields) to validate end-to-end output.

## Capabilities

### New Capabilities
- `rss-to-markdown-offline-tests`: Offline integration-style test coverage for the RSS-to-markdown package using local fixtures.

### Modified Capabilities
- `rss-to-markdown-scraper`: Clarify that processing must be testable offline using repository-local fixtures.

## Impact

- Tests and fixtures for the RSS-to-markdown package.
- Test runner configuration as needed to include offline integration tests.
