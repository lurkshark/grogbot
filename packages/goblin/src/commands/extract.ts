import { mkdir } from 'fs/promises';
import path from 'path';
import { parseFeed, parseItemDate, normalizeItem } from '../utils/rss.js';
import { buildSlug, hashSlug } from '../utils/slug.js';
import { writeMarkdownFile } from '../utils/frontmatter.js';

type SkippedItem = {
  title: string;
  reason: string;
};

export async function runExtract(pond: string, feedUrl: string): Promise<void> {
  const feed = await parseFeed(feedUrl);
  const ingestDir = path.join(pond, 'ingest');
  await mkdir(ingestDir, { recursive: true });

  const skipped: SkippedItem[] = [];
  let extractedCount = 0;

  for (const item of feed.items ?? []) {
    const title = item.title?.trim();
    if (!title) {
      skipped.push({ title: '(untitled)', reason: 'missing title' });
      continue;
    }

    const date = parseItemDate(item);
    if (!date) {
      skipped.push({ title, reason: 'missing publish date' });
      continue;
    }

    const url = item.link ?? item.guid ?? '';

    try {
      const { content } = await normalizeItem(item);
      const slug = buildSlug(date, title);
      const guid = hashSlug(slug);
      const outputPath = path.join(ingestDir, `${slug}.md`);

      await writeMarkdownFile(
        outputPath,
        {
          guid,
          slug,
          title,
          date: date.toISOString(),
          url,
        },
        content,
      );
      extractedCount += 1;
    } catch (error) {
      const reason = error instanceof Error ? error.message : 'unknown error';
      skipped.push({ title, reason });
    }
  }

  console.log(`Extracted ${extractedCount} item(s) into ${ingestDir}.`);
  if (skipped.length > 0) {
    console.log('Skipped items:');
    for (const item of skipped) {
      console.log(`- ${item.title}: ${item.reason}`);
    }
  }
}
