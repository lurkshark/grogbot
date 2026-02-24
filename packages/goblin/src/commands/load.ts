import { readdir } from 'fs/promises';
import path from 'path';
import { Search } from '@upstash/search';
import { readMarkdownFile } from '../utils/frontmatter.js';
import { chunkMarkdown } from '../utils/chunking.js';

type LoadOptions = {
  maxChunkSize?: number;
};

export async function runLoad(
  pond: string,
  namespace?: string,
  options: LoadOptions = {},
): Promise<void> {
  const resolvedNamespace = namespace ?? 'ingest';
  const sourceDir = path.join(pond, resolvedNamespace === 'ingest' ? 'ingest' : resolvedNamespace);

  const entries = await readdir(sourceDir, { withFileTypes: true });
  const files = entries.filter((entry) => entry.isFile() && entry.name.endsWith('.md'));

  const url = process.env.UPSTASH_SEARCH_REST_URL;
  const token = process.env.UPSTASH_SEARCH_REST_TOKEN;
  if (!url || !token) {
    throw new Error('UPSTASH_SEARCH_REST_URL and UPSTASH_SEARCH_REST_TOKEN are required.');
  }

  const search = new Search({ url, token });
  const maxChunkSize = options.maxChunkSize ?? 1500;

  const documents: Array<{
    id: string;
    content: {
      text: string;
    };
    metadata: {
      chunk_index: number;
      source_guid: string;
    };
  }> = [];

  for (const entry of files) {
    const filePath = path.join(sourceDir, entry.name);
    const { data, content } = await readMarkdownFile(filePath);
    const sourceGuid =
      (data.source_guid as string | undefined) ?? (data.guid as string | undefined);
    if (!sourceGuid) {
      throw new Error(`Missing guid in ${filePath}`);
    }

    const chunks = chunkMarkdown(content, { maxChunkSize, overlapRatio: 0.1 });
    chunks.forEach((chunk, index) => {
      documents.push({
        id: `${sourceGuid}-${index}`,
        content: {
          text: chunk,
        },
        metadata: {
          chunk_index: index,
          source_guid: sourceGuid,
        },
      });
    });
  }

  if (documents.length === 0) {
    console.log(`No markdown files found in ${sourceDir}.`);
    return;
  }

  const index = search.index(resolvedNamespace);
  await index.upsert(documents);

  console.log(
    `Loaded ${documents.length} chunk(s) from ${files.length} file(s) into ${resolvedNamespace}.`,
  );
}
