import { parseArgs } from "node:util";
import { scrapeFeed, type ScrapeOptions } from "./scraper.js";

type ParsedArgs = {
  values: {
    out?: string;
    overwrite?: boolean;
    limit?: number;
  };
  positionals: string[];
};

const USAGE = `goblin scrape <feed-url> [--out <dir>] [--overwrite] [--limit <n>]`;

export async function run(argv: string[]): Promise<void> {
  const [command, ...rest] = argv;
  if (!command || command === "--help" || command === "-h") {
    printUsage();
    return;
  }

  if (command !== "scrape") {
    throw new Error(`Unknown command: ${command}`);
  }

  const parsed = parseArgs({
    args: rest,
    allowPositionals: true,
    options: {
      out: {
        type: "string",
        short: "o",
      },
      overwrite: {
        type: "boolean",
      },
      limit: {
        type: "string",
      },
    },
  }) as ParsedArgs;

  const feedUrl = parsed.positionals[0];
  if (!feedUrl) {
    throw new Error("Missing feed URL.");
  }

  const limitText = parsed.values.limit;
  const limitValue = limitText ? Number(limitText) : undefined;
  if (limitText && (!Number.isFinite(limitValue ?? 0) || (limitValue ?? 0) <= 0)) {
    throw new Error("--limit must be a positive number.");
  }

  const options: ScrapeOptions = {
    outputDir: parsed.values.out,
    overwrite: Boolean(parsed.values.overwrite),
    limit: limitValue,
  };

  const summary = await scrapeFeed(feedUrl, options);
  const skipped = summary.skipped > 0 ? `, skipped ${summary.skipped}` : "";
  console.log(`Processed ${summary.total} items, wrote ${summary.written}${skipped}.`);
}

function printUsage(): void {
  console.log(USAGE);
}
