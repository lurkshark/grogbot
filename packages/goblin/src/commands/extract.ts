import { mkdir, readdir, writeFile } from 'fs/promises';
import path from 'path';
import pLimit from 'p-limit';
import YAML from 'yaml';
import { readMarkdownFile, writeMarkdownFile } from '../utils/frontmatter.js';
import { hashSlug } from '../utils/slug.js';
import { DEFAULT_MODEL, runPrompt } from '../utils/ai.js';

type ExtractOptions = {
  model?: string;
};

export async function runExtract(
  pond: string,
  namespace: string,
  prompt: string,
  options: ExtractOptions = {},
): Promise<void> {
  const ingestDir = path.join(pond, 'ingest');
  const outputDir = path.join(pond, namespace);
  await mkdir(outputDir, { recursive: true });

  const entries = await readdir(ingestDir, { withFileTypes: true });
  const files = entries.filter((entry) => entry.isFile() && entry.name.endsWith('.md'));

  const model = options.model ?? DEFAULT_MODEL;
  const limit = pLimit(8);

  const tasks = files.map((entry) =>
    limit(async () => {
      const filePath = path.join(ingestDir, entry.name);
      const { data, content } = await readMarkdownFile(filePath);
      const sourceSlug = data.slug as string | undefined;
      const sourceGuid = data.guid as string | undefined;
      if (!sourceSlug || !sourceGuid) {
        throw new Error(`Missing slug or guid in ${filePath}`);
      }
      const extractSlug = `${sourceSlug}--${namespace}`;
      const extractGuid = hashSlug(extractSlug);

      const composedPrompt = `${prompt}\n\n${content}`;
      const generated = await runPrompt(composedPrompt, model);

      const outputPath = path.join(outputDir, `${extractSlug}.md`);
      await writeMarkdownFile(
        outputPath,
        {
          guid: extractGuid,
          slug: extractSlug,
          source_guid: sourceGuid,
          source_slug: sourceSlug,
        },
        generated,
      );
    }),
  );

  await Promise.all(tasks);

  const infoPath = path.join(pond, `${namespace}-extract-info.yaml`);
  const info = {
    namespace,
    model,
    prompt,
    generated_at: new Date().toISOString(),
  };
  await writeFile(infoPath, YAML.stringify(info), 'utf8');

  console.log(`Extracted ${files.length} item(s) into ${outputDir}.`);
}
