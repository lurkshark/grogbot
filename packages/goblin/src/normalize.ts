import type { NormalizedFeedItem } from "./index.js";

type FeedItem = {
  title?: string;
  link?: string;
  guid?: string;
  isoDate?: string;
  pubDate?: string;
  creator?: string;
  author?: string;
  categories?: string[];
  content?: string;
  summary?: string;
  [key: string]: unknown;
};

const contentEncodedKey = "content:encoded" as const;

export function normalizeFeedItem(
  item: FeedItem,
  source: string,
): NormalizedFeedItem {
  const title = item.title?.trim() || item.link?.trim() || "Untitled";
  const link = item.link?.trim() || "";
  const guid = item.guid?.trim() || link || title;
  const date = resolveDate(item);
  const content = resolveContent(item);
  const author = item.creator ?? item.author;
  const categories = Array.isArray(item.categories)
    ? item.categories.map((category) => category.trim()).filter(Boolean)
    : undefined;

  return {
    title,
    date,
    link,
    guid,
    author: author?.trim() || undefined,
    categories: categories && categories.length > 0 ? categories : undefined,
    source,
    content,
  };
}

function resolveDate(item: FeedItem): string {
  if (item.isoDate) {
    return new Date(item.isoDate).toISOString();
  }
  if (item.pubDate) {
    const parsed = new Date(item.pubDate);
    if (!Number.isNaN(parsed.valueOf())) {
      return parsed.toISOString();
    }
  }
  return new Date().toISOString();
}

function resolveContent(item: FeedItem): string {
  const encoded = item[contentEncodedKey];
  if (typeof encoded === "string" && encoded.trim()) {
    return encoded.trim();
  }
  if (typeof item.content === "string" && item.content.trim()) {
    return item.content.trim();
  }
  if (typeof item.summary === "string" && item.summary.trim()) {
    return item.summary.trim();
  }
  return "";
}
