import matter from 'gray-matter';
import { readFile, writeFile } from 'fs/promises';

export type FrontmatterData = Record<string, unknown>;

export async function readMarkdownFile(path: string): Promise<{
  data: FrontmatterData;
  content: string;
}> {
  const raw = await readFile(path, 'utf8');
  const parsed = matter(raw);
  return {
    data: parsed.data as FrontmatterData,
    content: parsed.content.trim(),
  };
}

export async function writeMarkdownFile(
  path: string,
  data: FrontmatterData,
  content: string,
): Promise<void> {
  const normalizedContent = content.trimEnd() + '\n';
  const output = matter.stringify(normalizedContent, data);
  await writeFile(path, output, 'utf8');
}
