# @grogbot/goblin

CLI tooling for the Grogbot RSS → extract → transform → load pipeline.

## Usage

```bash
pnpm --filter @grogbot/goblin build

goblin extract <pond> <feed-url>

goblin transform <pond> <namespace> <prompt> [--model <model>]

goblin load <pond> [namespace] [--max-chunk-size <size>]
```

### Environment variables

- `OPENROUTER_API_KEY` (required for `transform`)
- `UPSTASH_SEARCH_REST_URL` (required for `load`)
- `UPSTASH_SEARCH_REST_TOKEN` (required for `load`)
