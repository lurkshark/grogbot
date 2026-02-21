import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import Parser from "rss-parser";
import { normalizeFeedItem } from "./normalize.js";
import { writeFeedItem } from "./writer.js";

export type ScrapeOptions = {
  outputDir?: string;
  overwrite?: boolean;
  limit?: number;
};

export type ScrapeSummary = {
  total: number;
  written: number;
  skipped: number;
};

export async function scrapeFeed(
  feedUrl: string,
  options: ScrapeOptions,
): Promise<ScrapeSummary> {
  const parser = new Parser({
    customFields: {
      item: ["content:encoded"],
    },
  });

  const { feed, source } = await loadFeed(parser, feedUrl);
  const items = feed.items ?? [];
  const limitedItems =
    typeof options.limit === "number" ? items.slice(0, options.limit) : items;

  let written = 0;
  let skipped = 0;

  for (const item of limitedItems) {
    const normalized = normalizeFeedItem(item as unknown as Record<string, unknown>, source);
    const result = await writeFeedItem(normalized, {
      outputDir: options.outputDir,
      overwrite: options.overwrite ?? false,
    });
    if (result === "written") {
      written += 1;
    } else {
      skipped += 1;
    }
  }

  return {
    total: limitedItems.length,
    written,
    skipped,
  };
}

async function loadFeed(
  parser: Parser,
  feedUrl: string,
): Promise<{ feed: Parser.Output<Record<string, unknown>>; source: string }> {
  if (isHttpUrl(feedUrl)) {
    const feed = await parser.parseURL(feedUrl);
    return { feed, source: feedUrl };
  }

  const localPath = resolveLocalPath(feedUrl);
  const xml = await readFile(localPath, "utf8");
  const feed = await parser.parseString(xml);
  return { feed, source: pathToFileURL(localPath).href };
}

function isHttpUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

function resolveLocalPath(value: string): string {
  if (value.startsWith("file://")) {
    return fileURLToPath(new URL(value));
  }
  return path.resolve(process.cwd(), value);
}
