## 1. Rename active workspace packages

- [x] 1.1 Rename `packages/search-core` to `packages/search` and update its package metadata so the distribution name becomes `grogbot-search` while the module remains `grogbot_search`
- [x] 1.2 Rename `packages/web` to `packages/app` and update its package metadata so the distribution name becomes `grogbot-app` and the module becomes `grogbot_app`
- [x] 1.3 Update the root workspace configuration and source declarations to reference `packages/search`, `packages/cli`, and `packages/app` only

## 2. Remove the standalone API surface

- [x] 2.1 Delete the `packages/api` package and remove all active workspace/package references to `grogbot-api`
- [x] 2.2 Remove or update current in-repo references to the retired JSON API endpoints so the active repository no longer documents or imports that surface

## 3. Update verification and documentation

- [x] 3.1 Update app imports/tests and any current package-oriented commands to use `grogbot_app`, `grogbot-app`, and the renamed package paths
- [x] 3.2 Update current documentation to describe the new canonical package structure and explicitly note that archived OpenSpec artifacts may still reference historical names
- [x] 3.3 Regenerate workspace lock/package state as needed and run the relevant test suites or validation commands against the renamed active packages
