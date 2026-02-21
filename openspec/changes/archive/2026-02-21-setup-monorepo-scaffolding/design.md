## Context

The repository is currently a single project with no workspace structure. We need a monorepo layout to host multiple TypeScript packages with shared tooling. The first package is a placeholder named `goblin`, intended to become an RSS-to-markdown scraper tool.

## Goals / Non-Goals

**Goals:**
- Establish a pnpm-based TypeScript monorepo that supports multiple packages.
- Provide a consistent package layout and shared configuration for TypeScript, linting, and formatting.
- Create a placeholder `goblin` package with minimal structure to evolve into an RSS scraper.

**Non-Goals:**
- Implement the RSS scraping functionality or markdown storage logic.
- Define runtime behavior or CLI interfaces for `goblin`.
- Introduce CI/CD or release automation at this stage.

## Decisions

- **Use pnpm workspaces** to manage packages and dependencies. This aligns with fast installs and strict dependency isolation.
  - *Alternatives considered:* npm workspaces (less strict node_modules layout), Yarn workspaces (different tooling expectations).
- **Adopt a `packages/` directory layout** with each package self-contained (`packages/goblin`). This is a common, discoverable structure and scales well for more packages.
  - *Alternatives considered:* `apps/`/`libs/` split (more opinionated than needed now), flat root package (does not scale).
- **Centralize TypeScript configuration** with a root `tsconfig.base.json` and per-package `tsconfig.json` extending it. This ensures consistent compiler settings while allowing package-specific tweaks later.
  - *Alternatives considered:* fully independent per-package configs (harder to keep consistent).
- **Provide minimal `goblin` package scaffolding** (entry point, package.json, tsconfig) without implementation. This keeps focus on the monorepo foundation and avoids premature functionality.
  - *Alternatives considered:* implement basic RSS parsing (out of scope for this change).

## Risks / Trade-offs

- **Risk:** Overly strict shared tooling may block package-specific needs later. → **Mitigation:** allow per-package overrides in config.
- **Risk:** Placeholder package could be mistaken for complete functionality. → **Mitigation:** keep README or package metadata explicit about placeholder status.
