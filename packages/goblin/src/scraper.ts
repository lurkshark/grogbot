import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import Parser from "rss-parser";
import { normalizeFeedItem } from "./normalize.js";
import { writeFeedItem } from "./writer.js";

export type ScrapeOptions = {
  outputDir?: string;
  overwrite?: boolean;
  maxPosts?: number;
};

export type ScrapeSummary = {
  total: number;
  written: number;
  skipped: number;
};

type LoadFeedResult = {
  feed: Parser.Output<Record<string, unknown>>;
  source: string;
  xml: string;
  baseUrl: string;
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

  const maxPosts = options.maxPosts ?? 100;
  let nextUrl: string | null = feedUrl;
  const visited = new Set<string>();
  let total = 0;
  let written = 0;
  let skipped = 0;

  while (nextUrl && total < maxPosts) {
    if (visited.has(nextUrl)) {
      break;
    }
    visited.add(nextUrl);

    const { feed, source, xml, baseUrl } = await loadFeed(parser, nextUrl);
    const items = (feed.items ?? []) as Array<Record<string, unknown>>;
    const pageBase = source;

    for (const item of items) {
      if (total >= maxPosts) {
        break;
      }
      total += 1;
      const normalized = normalizeFeedItem(item, pageBase);
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

    const nextPage = findNextPageUrl(xml, baseUrl);
    nextUrl = nextPage && !visited.has(nextPage) ? nextPage : null;
  }

  return {
    total,
    written,
    skipped,
  };
}

async function loadFeed(parser: Parser, feedUrl: string): Promise<LoadFeedResult> {
  if (isHttpUrl(feedUrl)) {
    const response = await fetch(feedUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch feed: ${response.status} ${response.statusText}`);
    }
    const xml = await response.text();
    const baseUrl = response.url || feedUrl;
    const feed = await parser.parseString(xml);
    return { feed, source: baseUrl, xml, baseUrl };
  }

  const localPath = resolveLocalPath(feedUrl);
  const xml = await readFile(localPath, "utf8");
  const feed = await parser.parseString(xml);
  const baseUrl = pathToFileURL(localPath).href;
  return { feed, source: baseUrl, xml, baseUrl };
}

function findNextPageUrl(xml: string, baseUrl: string): string | null {
  const linkTagRegex = /<\s*(?:atom:link|link)\b[^>]*>/gi;
  const matches = xml.matchAll(linkTagRegex);

  for (const match of matches) {
    const tag = match[0];
    const attrs = parseAttributes(tag);
    const rel = attrs.rel?.toLowerCase();
    if (rel !== "next" && rel !== "older") {
      continue;
    }
    const href = attrs.href;
    if (!href) {
      continue;
    }
    try {
      return new URL(href, baseUrl).href;
    } catch {
      continue;
    }
  }

  return null;
}

function parseAttributes(tag: string): Record<string, string> {
  const attributes: Record<string, string> = {};
  const attrRegex = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*["']([^"']*)["']/g;
  let match: RegExpExecArray | null = attrRegex.exec(tag);
  while (match) {
    attributes[match[1].toLowerCase()] = match[2];
    match = attrRegex.exec(tag);
  }
  return attributes;
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
