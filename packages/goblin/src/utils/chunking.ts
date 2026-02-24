export type ChunkOptions = {
  maxChunkSize?: number;
  overlapRatio?: number;
};

function splitIntoBlocks(markdown: string): string[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: string[] = [];
  let current: string[] = [];
  const headingRegex = /^#{1,6}\s+/;

  const pushCurrent = () => {
    if (current.length > 0) {
      const block = current.join('\n').trim();
      if (block) {
        blocks.push(block);
      }
      current = [];
    }
  };

  for (const line of lines) {
    if (headingRegex.test(line.trim())) {
      pushCurrent();
    }
    current.push(line);
  }

  pushCurrent();

  return blocks;
}

function splitLargeBlock(block: string, maxChunkSize: number): string[] {
  if (block.length <= maxChunkSize) {
    return [block.trim()];
  }

  const lines = block.split(/\r?\n/);
  const headingLine = lines[0].trim();
  const hasHeading = /^#{1,6}\s+/.test(headingLine);
  const body = hasHeading ? lines.slice(1).join('\n').trim() : block.trim();
  const paragraphs = body.split(/\n{2,}/);

  const chunks: string[] = [];
  let current = hasHeading ? headingLine : '';

  const flush = () => {
    const trimmed = current.trim();
    if (trimmed) {
      chunks.push(trimmed);
    }
    current = hasHeading ? headingLine : '';
  };

  for (const paragraph of paragraphs) {
    const segment = paragraph.trim();
    if (!segment) {
      continue;
    }
    const separator = current && current !== headingLine ? '\n\n' : current ? '\n\n' : '';
    if ((current + separator + segment).length > maxChunkSize && current !== (hasHeading ? headingLine : '')) {
      flush();
    }
    current = current ? `${current}${separator}${segment}` : segment;
  }

  flush();

  return chunks;
}

function applyOverlap(chunks: string[], overlapRatio: number): string[] {
  if (chunks.length <= 1) {
    return chunks;
  }
  const overlapped: string[] = [chunks[0]];
  for (let i = 1; i < chunks.length; i += 1) {
    const previous = overlapped[i - 1];
    const overlapSize = Math.floor(previous.length * overlapRatio);
    const overlap = overlapSize > 0 ? previous.slice(-overlapSize) : '';
    const prefix = overlap ? `${overlap}\n\n` : '';
    overlapped.push(`${prefix}${chunks[i]}`.trim());
  }
  return overlapped;
}

export function chunkMarkdown(markdown: string, options: ChunkOptions = {}): string[] {
  const maxChunkSize = options.maxChunkSize ?? 1500;
  const overlapRatio = options.overlapRatio ?? 0.1;

  const blocks = splitIntoBlocks(markdown);
  const normalizedBlocks = blocks.flatMap((block) => splitLargeBlock(block, maxChunkSize));

  const chunks: string[] = [];
  let current = '';

  const pushCurrent = () => {
    if (current.trim()) {
      chunks.push(current.trim());
    }
    current = '';
  };

  for (const block of normalizedBlocks) {
    const separator = current ? '\n\n' : '';
    if (current && current.length + separator.length + block.length > maxChunkSize) {
      pushCurrent();
    }
    current = current ? `${current}${separator}${block}` : block;
  }

  pushCurrent();

  return applyOverlap(chunks, overlapRatio);
}
