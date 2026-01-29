/**
 * Atlas MCP — Background Indexer Worker
 *
 * Indexes Markdown files and database records into the local search DB.
 * Run with: bun run src/scripts/index-worker.ts [directory]
 *
 * Privacy-first: all processing happens locally.
 */

import fs from "node:fs";
import path from "node:path";
import { openDatabase, initSchema, upsertDocument, upsertEmbedding } from "../db/schema.js";
import { getEmbedding, checkOllamaHealth } from "../embed/ollama.js";
import { chunkText, extractTitle } from "../utils/chunker.js";

const SUPPORTED_EXTENSIONS = new Set([".md", ".mdx", ".txt", ".rst"]);

interface IndexStats {
  files_scanned: number;
  chunks_indexed: number;
  embeddings_created: number;
  errors: number;
  elapsed_ms: number;
}

/** Recursively collect all supported files from a directory. */
function collectFiles(dir: string): string[] {
  const results: string[] = [];

  function walk(current: string) {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) {
        // Skip hidden dirs and node_modules
        if (!entry.name.startsWith(".") && entry.name !== "node_modules") {
          walk(full);
        }
      } else if (SUPPORTED_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
        results.push(full);
      }
    }
  }

  walk(dir);
  return results;
}

async function indexFile(
  db: ReturnType<typeof openDatabase>,
  filePath: string,
  embedEnabled: boolean,
): Promise<{ chunks: number; embeddings: number }> {
  const content = fs.readFileSync(filePath, "utf-8");
  const title = extractTitle(content);
  const chunks = chunkText(content);

  let embeddingsCreated = 0;

  for (const chunk of chunks) {
    const docId = upsertDocument(db, {
      source_path: filePath,
      title,
      content: chunk.text,
      chunk_index: chunk.index,
      metadata_json: JSON.stringify({
        ext: path.extname(filePath),
        size: content.length,
      }),
    });

    if (embedEnabled) {
      try {
        const embedding = await getEmbedding(chunk.text);
        upsertEmbedding(db, docId, embedding);
        embeddingsCreated++;
      } catch (e) {
        console.error(`  Embedding failed for chunk ${chunk.index}: ${(e as Error).message}`);
      }
    }
  }

  return { chunks: chunks.length, embeddings: embeddingsCreated };
}

async function main() {
  const targetDir = process.argv[2] ?? path.resolve(import.meta.dir ?? ".", "../../../../docs");
  const dbPath = process.env.ATLAS_SEARCH_DB;

  console.log("Atlas MCP Indexer");
  console.log(`  Target:   ${targetDir}`);
  console.log(`  Database: ${dbPath ?? "(default)"}`);

  if (!fs.existsSync(targetDir)) {
    console.error(`Directory not found: ${targetDir}`);
    process.exit(1);
  }

  // Check Ollama availability
  const ollamaStatus = await checkOllamaHealth();
  const embedEnabled = ollamaStatus.ok;
  if (!embedEnabled) {
    console.warn(`  Ollama: ${ollamaStatus.error}`);
    console.warn("  Proceeding with keyword indexing only (no embeddings).");
  } else {
    console.log("  Ollama: connected");
  }

  const db = openDatabase(dbPath);
  initSchema(db);

  const files = collectFiles(targetDir);
  console.log(`  Found ${files.length} files to index.\n`);

  const start = Date.now();
  const stats: IndexStats = {
    files_scanned: files.length,
    chunks_indexed: 0,
    embeddings_created: 0,
    errors: 0,
    elapsed_ms: 0,
  };

  for (const filePath of files) {
    const rel = path.relative(targetDir, filePath);
    try {
      const result = await indexFile(db, filePath, embedEnabled);
      stats.chunks_indexed += result.chunks;
      stats.embeddings_created += result.embeddings;
      console.log(`  [OK] ${rel} (${result.chunks} chunks, ${result.embeddings} embeddings)`);
    } catch (e) {
      stats.errors++;
      console.error(`  [ERR] ${rel}: ${(e as Error).message}`);
    }
  }

  stats.elapsed_ms = Date.now() - start;

  db.close();

  console.log("\n--- Index Complete ---");
  console.log(`  Files:      ${stats.files_scanned}`);
  console.log(`  Chunks:     ${stats.chunks_indexed}`);
  console.log(`  Embeddings: ${stats.embeddings_created}`);
  console.log(`  Errors:     ${stats.errors}`);
  console.log(`  Time:       ${stats.elapsed_ms}ms`);
}

main().catch((e) => {
  console.error("Indexer failed:", e);
  process.exit(1);
});
