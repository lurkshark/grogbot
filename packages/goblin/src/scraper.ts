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

  const feed = await parser.parseURL(feedUrl);
  const items = feed.items ?? [];
  const limitedItems =
    typeof options.limit === "number" ? items.slice(0, options.limit) : items;

  let written = 0;
  let skipped = 0;

  for (const item of limitedItems) {
    const normalized = normalizeFeedItem(item as unknown as Record<string, unknown>, feedUrl);
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
