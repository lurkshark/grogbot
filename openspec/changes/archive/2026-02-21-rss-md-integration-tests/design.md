## Context

The RSS-to-markdown package currently lacks end-to-end coverage that exercises parsing through Markdown output. The tests must run fully offline, rely on repository-local fixtures, and be executable by agents without any permission to access files outside the project.

## Goals / Non-Goals

**Goals:**
- Add integration-style tests that invoke the RSS-to-markdown flow against local feed fixtures and assert Markdown output.
- Ensure tests run without internet access and only read/write within the repository.
- Cover representative feed variants (typical RSS items, missing fields) to validate parsing and formatting behavior.

**Non-Goals:**
- Introducing live network calls or remote feeds in tests.
- Changing the core RSS-to-markdown behavior beyond what is required to make it testable offline.
- Building a full fixture generation pipeline or complex test harness beyond repository-local files.

## Decisions

- **Use local fixture files for RSS input and expected Markdown output.** This keeps tests deterministic, offline, and compatible with constrained agents. Alternative: mocking HTTP requests or using recorded HTTP fixtures. Rejected because it introduces additional harness complexity and may still require filesystem access outside the repo for caches.
- **Run the same entrypoint or public API used by the package consumers.** Integration-style coverage should exercise the actual flow, not a reimplementation. Alternative: unit-level parsing tests. Rejected because it would not validate end-to-end output.
- **Locate fixtures within the package test directory.** This ensures tests are self-contained and permissions remain within the repo. Alternative: shared fixtures at the repo root. Rejected to avoid cross-package coupling.

## Risks / Trade-offs

- Fixture maintenance overhead as outputs change → Keep fixtures minimal, cover only representative cases.
- Tests may become brittle if Markdown formatting changes → Use stable golden outputs and update deliberately when behavior changes.
