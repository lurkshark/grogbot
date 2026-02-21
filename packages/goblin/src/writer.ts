import { mkdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import TurndownService from "turndown";
import type { NormalizedFeedItem } from "./index.js";

type WriteOptions = {
  outputDir?: string;
  overwrite: boolean;
};

type WriteResult = "written" | "skipped";

export async function writeFeedItem(
  item: NormalizedFeedItem,
  options: WriteOptions,
): Promise<WriteResult> {
  const outputDir = options.outputDir ?? process.cwd();
  await mkdir(outputDir, { recursive: true });
  const filename = buildFilename(item);
  const targetPath = path.join(outputDir, filename);

  if (!options.overwrite) {
    const exists = await fileExists(targetPath);
    if (exists) {
      return "skipped";
    }
  }

  const content = buildMarkdown(item);
  await writeFile(targetPath, content, "utf8");
  return "written";
}

function buildFilename(item: NormalizedFeedItem): string {
  const datePrefix = item.date.slice(0, 10);
  const slugSource = item.title || item.guid || "post";
  const slug = slugify(slugSource);
  return `${datePrefix}-${slug}.md`;
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 80) || "post";
}

function buildMarkdown(item: NormalizedFeedItem): string {
  const frontmatter: Record<string, string | string[] | undefined> = {
    title: item.title,
    date: item.date,
    link: item.link || undefined,
    guid: item.guid,
    author: item.author,
    categories: item.categories,
    source: item.source,
  };

  const lines: string[] = ["---"]; 
  for (const [key, value] of Object.entries(frontmatter)) {
    if (value === undefined) {
      continue;
    }
    if (Array.isArray(value)) {
      lines.push(`${key}:`);
      for (const entry of value) {
        lines.push(`  - ${escapeYaml(entry)}`);
      }
    } else {
      lines.push(`${key}: ${escapeYaml(value)}`);
    }
  }
  const body = convertContentToMarkdown(item.content);
  lines.push("---", "", body, "");
  return `${lines.join("\n")}`;
}

function convertContentToMarkdown(content: string): string {
  const trimmed = content.trim();
  if (!trimmed) {
    return "";
  }
  if (looksLikeHtml(trimmed)) {
    const service = new TurndownService({
      codeBlockStyle: "fenced",
      emDelimiter: "*",
      headingStyle: "atx",
    });
    return service.turndown(trimmed);
  }
  return trimmed;
}

function looksLikeHtml(content: string): boolean {
  return /<\/?[a-z][\s\S]*>/i.test(content);
}

function escapeYaml(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '""';
  }
  if (/[:#\n\-]/.test(trimmed)) {
    return JSON.stringify(trimmed);
  }
  return trimmed;
}

async function fileExists(targetPath: string): Promise<boolean> {
  try {
    const stats = await stat(targetPath);
    return stats.isFile();
  } catch {
    return false;
  }
}
