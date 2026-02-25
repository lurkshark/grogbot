import { mkdir, readdir, writeFile } from 'fs/promises';
import path from 'path';
import pLimit from 'p-limit';
import YAML from 'yaml';
import { readMarkdownFile, writeMarkdownFile } from '../utils/frontmatter.js';
import { hashSlug } from '../utils/slug.js';
import { DEFAULT_MODEL, runPrompt } from '../utils/ai.js';

type TransformOptions = {
  model?: string;
};

export async function runTransform(
  stagingDirectory: string,
  namespace: string,
  prompt: string,
  options: TransformOptions = {},
): Promise<void> {
  const extractDir = path.join(stagingDirectory, 'extract');
  const outputDir = path.join(stagingDirectory, namespace);
  await mkdir(outputDir, { recursive: true });

  const entries = await readdir(extractDir, { withFileTypes: true });
  const files = entries.filter((entry) => entry.isFile() && entry.name.endsWith('.md'));

  const model = options.model ?? DEFAULT_MODEL;
  const limit = pLimit(8);

  const tasks = files.map((entry) =>
    limit(async () => {
      const filePath = path.join(extractDir, entry.name);
      const { data, content } = await readMarkdownFile(filePath);
      const sourceSlug = data.slug as string | undefined;
      const sourceGuid = data.guid as string | undefined;
      if (!sourceSlug || !sourceGuid) {
        throw new Error(`Missing slug or guid in ${filePath}`);
      }
      const transformSlug = `${sourceSlug}--${namespace}`;
      const transformGuid = hashSlug(transformSlug);

      const composedPrompt = `${prompt}\n\n${content}`;
      const generated = await runPrompt(composedPrompt, model);

      const outputPath = path.join(outputDir, `${transformSlug}.md`);
      await writeMarkdownFile(
        outputPath,
        {
          guid: transformGuid,
          slug: transformSlug,
          source_guid: sourceGuid,
          source_slug: sourceSlug,
        },
        generated,
      );
    }),
  );

  await Promise.all(tasks);

  const infoPath = path.join(stagingDirectory, `${namespace}-transform-info.yaml`);
  const info = {
    namespace,
    model,
    prompt,
    generated_at: new Date().toISOString(),
  };
  await writeFile(infoPath, YAML.stringify(info), 'utf8');

  console.log(`Transformed ${files.length} item(s) into ${outputDir}.`);
}
