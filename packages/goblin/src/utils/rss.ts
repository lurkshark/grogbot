import Parser from 'rss-parser';
import { JSDOM } from 'jsdom';
import { Readability } from '@mozilla/readability';
import TurndownService from 'turndown';

type RssItem = Parser.Item & {
  'content:encoded'?: string;
};

const parser = new Parser<{}, RssItem>();
const turndown = new TurndownService({
  codeBlockStyle: 'fenced',
});

export type NormalizedItem = {
  title: string;
  date: Date;
  url: string;
  content: string;
  contentSource: 'rss' | 'readability';
};

export async function parseFeed(feedUrl: string): Promise<Parser.Output<RssItem>> {
  return parser.parseURL(feedUrl);
}

export function parseItemDate(item: RssItem): Date | null {
  const dateValue = item.isoDate ?? item.pubDate ?? '';
  if (!dateValue) {
    return null;
  }
  const parsed = new Date(dateValue);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function extractRssContent(item: RssItem): string | null {
  const candidate =
    (item['content:encoded'] as string | undefined) ??
    item.content ??
    item.summary ??
    item.contentSnippet;
  if (!candidate) {
    return null;
  }
  const trimmed = candidate.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function looksLikeHtml(content: string): boolean {
  return /<\/?[a-z][\s\S]*>/i.test(content);
}

export function htmlToMarkdown(html: string): string {
  return turndown.turndown(html);
}

export async function fetchReadableMarkdown(url: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }
  const html = await response.text();
  const dom = new JSDOM(html, { url });
  const reader = new Readability(dom.window.document);
  const article = reader.parse();
  if (!article?.content) {
    throw new Error(`Readability failed for ${url}`);
  }
  return htmlToMarkdown(article.content);
}

export async function normalizeItem(item: RssItem): Promise<{
  content: string;
  contentSource: NormalizedItem['contentSource'];
}> {
  const rssContent = extractRssContent(item);
  if (rssContent) {
    const content = looksLikeHtml(rssContent) ? htmlToMarkdown(rssContent) : rssContent;
    return {
      content,
      contentSource: 'rss',
    };
  }
  if (!item.link) {
    throw new Error('Item missing link for readability fetch');
  }
  const content = await fetchReadableMarkdown(item.link);
  return {
    content,
    contentSource: 'readability',
  };
}
