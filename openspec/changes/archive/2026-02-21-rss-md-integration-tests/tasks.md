## 1. Locate entrypoints and test harness

- [x] 1.1 Identify the RSS-to-markdown CLI or public API entrypoint to exercise end-to-end
- [x] 1.2 Confirm existing test runner setup and where package tests live

## 2. Add repository-local fixtures

- [x] 2.1 Create RSS input fixtures (typical feed and missing optional fields)
- [x] 2.2 Create expected Markdown outputs for each fixture
- [x] 2.3 Ensure fixture paths resolve within the package directory

## 3. Implement offline integration tests

- [x] 3.1 Add integration-style tests that run the entrypoint against fixtures
- [x] 3.2 Assert generated Markdown matches expected outputs
- [x] 3.3 Ensure tests do not access network or files outside the repository

## 4. Validate and document test execution

- [x] 4.1 Run the test suite locally and verify offline tests pass
- [x] 4.2 Document how to run the offline integration tests (if needed)
