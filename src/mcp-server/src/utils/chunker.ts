/**
 * Atlas MCP — Text Chunking Utilities
 *
 * Splits documents into overlapping chunks for embedding.
 * Preserves paragraph boundaries when possible.
 */

export interface Chunk {
  text: string;
  index: number;
}

const DEFAULT_CHUNK_SIZE = 512;
const DEFAULT_OVERLAP = 64;

/**
 * Split text into chunks by paragraph boundaries with overlap.
 * Attempts to break at double-newlines first, then at sentence boundaries.
 */
export function chunkText(
  text: string,
  maxChunkSize: number = DEFAULT_CHUNK_SIZE,
  overlap: number = DEFAULT_OVERLAP,
): Chunk[] {
  const cleaned = text.replace(/\r\n/g, "\n").trim();
  if (!cleaned) return [];

  if (cleaned.length <= maxChunkSize) {
    return [{ text: cleaned, index: 0 }];
  }

  const paragraphs = cleaned.split(/\n{2,}/);
  const chunks: Chunk[] = [];
  let current = "";
  let idx = 0;

  for (const para of paragraphs) {
    const trimmed = para.trim();
    if (!trimmed) continue;

    if (current.length + trimmed.length + 2 > maxChunkSize && current) {
      chunks.push({ text: current.trim(), index: idx++ });
      // Keep overlap from end of previous chunk
      const words = current.split(/\s+/);
      const overlapWords = words.slice(-Math.ceil(overlap / 5));
      current = overlapWords.join(" ") + "\n\n" + trimmed;
    } else {
      current = current ? current + "\n\n" + trimmed : trimmed;
    }
  }

  if (current.trim()) {
    chunks.push({ text: current.trim(), index: idx });
  }

  return chunks;
}

/** Extract a title from markdown content (first # heading or first line). */
export function extractTitle(content: string): string {
  const match = content.match(/^#\s+(.+)$/m);
  if (match) return match[1].trim();
  const firstLine = content.split("\n")[0]?.trim() ?? "";
  return firstLine.slice(0, 100);
}
