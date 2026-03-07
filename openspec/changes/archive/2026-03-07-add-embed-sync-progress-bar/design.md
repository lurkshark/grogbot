## Context

`grogbot search document embed-sync` currently calls `SearchService.synchronize_document_embeddings(maximum=...)` and only prints a final JSON payload after all work completes. The bulk synchronization loop already operates per document inside `search-core`, which means the core package knows when total work is selected and when each document finishes, but it does not currently expose that progress to callers.

This change spans both `search-core` and `cli`:
- `search-core` must expose raw progress information without taking on terminal UI responsibilities.
- `cli` must render a progress bar and ETA while preserving the command's machine-readable final output.

The user explicitly wants progress-bar details and ETA computation to remain in the CLI package, not in `search-core`.

## Goals / Non-Goals

**Goals:**
- Allow bulk embedding synchronization callers to observe progress without changing the core embedding workflow.
- Keep terminal rendering, elapsed time tracking, and ETA calculation in `packages/cli`.
- Update `embed-sync` to show meaningful live progress while maintaining the current final JSON result.
- Scope progress updates to per-document completion so callback frequency stays low and aligns with the existing orchestration loop.

**Non-Goals:**
- Per-chunk or per-vector progress callbacks.
- Changing API or non-CLI embedding endpoints to render progress bars.
- Reworking embedding batch internals or changing how `embed_document_chunks` generates vectors.
- Providing perfectly smooth ETA for highly uneven document sizes.

## Decisions

### 1. `search-core` exposes an optional per-document progress callback

**Decision:** Extend `SearchService.synchronize_document_embeddings(...)` with an optional callback parameter that receives raw progress snapshots during a run.

**Rationale:** The service already owns document selection and the per-document embedding loop, so it is the natural place to emit progress facts. An optional callback preserves existing behavior for API callers that do not care about progress and avoids pushing orchestration into the CLI.

**Alternatives considered:**
- **CLI orchestrates embedding one document at a time:** rejected because it duplicates selection/orchestration logic outside `search-core`.
- **`search-core` renders progress directly:** rejected because terminal UI concerns belong in the CLI package.

### 2. Progress is reported once before work starts and once after each completed document

**Decision:** Emit an initial snapshot with total selected documents and zero completed work, then emit one update after each document finishes embedding.

**Rationale:** The CLI can initialize the progress bar with the true denominator immediately, and subsequent updates occur at a human-friendly cadence. This matches the user's preference for per-document callbacks and avoids excessive callback traffic.

**Alternatives considered:**
- **Per-chunk updates:** rejected because updates would be much more frequent and noisier than needed.
- **Only post-completion updates with no initial snapshot:** rejected because the CLI would not know the total upfront.

### 3. Progress snapshots contain raw counters, not formatted strings

**Decision:** The callback payload should include raw synchronization facts such as total selected documents, completed documents, and cumulative vectors created.

**Rationale:** Raw counters keep the `search-core` API presentation-neutral while giving the CLI enough information to compute ETA and show secondary status details.

**Alternatives considered:**
- **Passing formatted status text from `search-core`:** rejected because it bakes CLI presentation into the core package.
- **Passing only a completed-document tick:** rejected because the CLI would lose useful context such as total vectors created.

### 4. CLI progress renders on stderr and final JSON remains on stdout

**Decision:** The `embed-sync` command will display live progress on stderr and continue emitting the final `{ "vectors_created": ... }` JSON payload on stdout.

**Rationale:** This preserves current scriptability and machine-readable output while still providing an interactive progress experience for humans running the command in a terminal.

**Alternatives considered:**
- **Render progress on stdout:** rejected because it would corrupt JSON output for pipes and scripts.
- **Replace JSON with a human-only summary:** rejected because it changes existing command behavior.

### 5. CLI may add an explicit progress-rendering dependency if it imports one directly

**Decision:** If the implementation imports a progress UI library directly, `packages/cli` should declare that dependency explicitly rather than relying on transitive installation behavior.

**Rationale:** The CLI should own its presentation dependencies clearly.

## Risks / Trade-offs

**ETA may be noisy when document sizes vary widely** → Use per-document progress anyway because it keeps the design simple and aligns with current orchestration; show ETA as a best-effort estimate rather than a precise promise.

**Callback payload could become a de facto UI contract if underspecified** → Define the payload around neutral counters and document lifecycle milestones, not terminal formatting.

**Interactive progress output can interfere with automation if channels are mixed** → Keep live progress on stderr and final structured output on stdout.

## Migration Plan

- No data migration is required.
- Existing callers that do not pass a progress callback continue to receive the same integer return value and behavior.
- CLI users gain live progress output during `embed-sync`; scripts consuming stdout JSON remain compatible.

## Open Questions

- None currently; the boundary between raw progress callbacks in `search-core` and rendering in `cli` is clear.
