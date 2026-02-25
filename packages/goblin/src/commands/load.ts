import { readdir } from 'fs/promises';
import path from 'path';
import { Search } from '@upstash/search';
import { readMarkdownFile } from '../utils/frontmatter.js';
import { chunkMarkdown } from '../utils/chunking.js';

type LoadOptions = {
  maxChunkSize?: number;
};

export async function runLoad(
  stagingDirectory: string,
  namespace?: string,
  options: LoadOptions = {},
): Promise<void> {
  const resolvedNamespace = namespace ?? 'extract';
  const sourceDir = path.join(
    stagingDirectory,
    resolvedNamespace,
  );

  const entries = await readdir(sourceDir, { withFileTypes: true });
  const files = entries.filter((entry) => entry.isFile() && entry.name.endsWith('.md'));

  const url = process.env.UPSTASH_SEARCH_REST_URL;
  const token = process.env.UPSTASH_SEARCH_REST_TOKEN;
  if (!url || !token) {
    throw new Error('UPSTASH_SEARCH_REST_URL and UPSTASH_SEARCH_REST_TOKEN are required.');
  }

  const search = new Search({ url, token });
  const maxChunkSize = options.maxChunkSize ?? 2048;

  const documents: Array<{
    id: string;
    content: {
      text: string;
    };
    metadata: {
      chunkIndex: number;
      sourceGuid: string;
    };
  }> = [];

  for (const entry of files) {
    const filePath = path.join(sourceDir, entry.name);
    const { data, content } = await readMarkdownFile(filePath);
    const slug = path.parse(entry.name).name;
    const sourceGuid =
      (data.sourceGuid as string | undefined) ?? (data.guid as string | undefined);
    if (!sourceGuid) {
      throw new Error(`Missing guid in ${filePath}`);
    }

    const chunks = chunkMarkdown(content, { maxChunkSize, overlapRatio: 0.05 });
    chunks.forEach((chunk, index) => {
      documents.push({
        id: `${slug}-${index}`,
        content: {
          text: chunk,
        },
        metadata: {
          chunkIndex: index,
          sourceGuid: sourceGuid,
        },
      });
    });
  }

  if (documents.length === 0) {
    console.log(`No markdown files found in ${sourceDir}.`);
    return;
  }

  const index = search.index(resolvedNamespace);
  for (let start = 0; start < documents.length; start += 100) {
    const batch = documents.slice(start, start + 100);
    await index.upsert(batch);
  }

  console.log(
    `Loaded ${documents.length} chunk(s) from ${files.length} file(s) into ${resolvedNamespace}.`,
  );
}
