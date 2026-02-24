# @grogbot/goblin

CLI tooling for the Grogbot RSS → extract → store pipeline.

## Usage

```bash
pnpm --filter @grogbot/goblin build

goblin ingest <pond> <feed-url>

goblin extract <pond> <namespace> <prompt> [--model <model>]

goblin store <pond> [namespace] [--max-chunk-size <size>]
```

### Environment variables

- `OPENROUTER_API_KEY` (required for `extract`)
- `UPSTASH_SEARCH_REST_URL` (required for `store`)
- `UPSTASH_SEARCH_REST_TOKEN` (required for `store`)
