/**
 * Atlas MCP Server — Local Hybrid Search Knowledge Engine
 *
 * Exposes two tools via Model Context Protocol:
 *   - atlas_search       : Hybrid BM25 + vector search, returns token-efficient summaries
 *   - atlas_fetch_details: Fetches full text for a specific document (progressive disclosure)
 *
 * Design Principles:
 *   - Privacy-first: all data stays local, no external API calls for search
 *   - Token-efficient: ~95% reduction via local retrieval + snippet summaries
 *   - Progressive disclosure: summary first, full text on demand
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { openDatabase, initSchema } from "./db/schema.js";
import { hybridSearch, buildSearchSummary } from "./search/hybrid.js";
import type Database from "better-sqlite3";

// ---------- Database ----------

let db: Database.Database;

function ensureDb(): Database.Database {
  if (!db) {
    db = openDatabase();
    initSchema(db);
  }
  return db;
}

// ---------- MCP Server ----------

const server = new McpServer({
  name: "atlas-search",
  version: "0.1.0",
});

// Tool 1: atlas_search — Hybrid search with token-efficient output
server.tool(
  "atlas_search",
  "Search Atlas knowledge base using hybrid BM25 + vector search. Returns concise summaries (token-efficient). Use atlas_fetch_details for full text.",
  {
    query: z.string().min(1).describe("Search query (supports Arabic and English)"),
    top_k: z.number().int().min(1).max(10).default(3).describe("Number of results to return (default: 3)"),
  },
  async ({ query, top_k }) => {
    const database = ensureDb();

    try {
      // Count total documents for context
      const countRow = database.prepare("SELECT COUNT(*) AS cnt FROM documents").get() as { cnt: number };

      const results = await hybridSearch(database, query, top_k);
      const summary = buildSearchSummary(query, results, countRow.cnt);

      return {
        content: [
          {
            type: "text" as const,
            text: formatSearchOutput(summary),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Search error: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  },
);

// Tool 2: atlas_fetch_details — Progressive disclosure: get full document text
server.tool(
  "atlas_fetch_details",
  "Fetch full text of a document by ID. Use after atlas_search to get complete content for a specific result.",
  {
    document_id: z.number().int().positive().describe("Document ID from atlas_search results"),
  },
  async ({ document_id }) => {
    const database = ensureDb();

    try {
      const row = database
        .prepare(
          `SELECT id, source_path, title, content, chunk_index, metadata_json
           FROM documents WHERE id = ?`,
        )
        .get(document_id) as {
        id: number;
        source_path: string;
        title: string;
        content: string;
        chunk_index: number;
        metadata_json: string;
      } | undefined;

      if (!row) {
        return {
          content: [
            { type: "text" as const, text: `Document ${document_id} not found.` },
          ],
          isError: true,
        };
      }

      // Also fetch adjacent chunks for context
      const siblings = database
        .prepare(
          `SELECT id, chunk_index, content FROM documents
           WHERE source_path = ? AND chunk_index BETWEEN ? AND ?
           ORDER BY chunk_index`,
        )
        .all(row.source_path, row.chunk_index - 1, row.chunk_index + 1) as Array<{
        id: number;
        chunk_index: number;
        content: string;
      }>;

      const fullText = siblings.map((s) => s.content).join("\n\n---\n\n");

      return {
        content: [
          {
            type: "text" as const,
            text: [
              `# ${row.title}`,
              `Source: ${row.source_path}`,
              `Chunks: ${siblings.map((s) => s.chunk_index).join(", ")}`,
              "",
              fullText,
            ].join("\n"),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Fetch error: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  },
);

// ---------- Output Formatting ----------

function formatSearchOutput(summary: ReturnType<typeof buildSearchSummary>): string {
  if (summary.results.length === 0) {
    return `No results for "${summary.query}" (searched ${summary.total_candidates} documents)`;
  }

  const lines = [
    `Found ${summary.results.length} results (from ${summary.total_candidates} documents):`,
    "",
  ];

  for (const r of summary.results) {
    lines.push(`[${r.document_id}] ${r.title} (${r.match_type}, score: ${r.score})`);
    lines.push(`    ${r.source_path}`);
    lines.push(`    ${r.snippet}`);
    lines.push("");
  }

  lines.push("Use atlas_fetch_details with a document_id for full text.");

  return lines.join("\n");
}

// ---------- Start ----------

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Atlas MCP Server running on stdio");
}

main().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});
