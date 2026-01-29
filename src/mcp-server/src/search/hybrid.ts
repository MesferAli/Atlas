/**
 * Atlas MCP — Hybrid Search Engine
 *
 * Combines BM25 (FTS5) keyword search with cosine-distance vector search,
 * then applies local reranking to return only the Top-3 most relevant chunks.
 *
 * Token efficiency: returns distilled context instead of full documents,
 * reducing token consumption by ~95% compared to large context windows.
 */

import type Database from "better-sqlite3";
import { getEmbedding } from "../embed/ollama.js";
import { EMBEDDING_DIM } from "../db/schema.js";

export interface SearchResult {
  document_id: number;
  source_path: string;
  title: string;
  content: string;
  chunk_index: number;
  score: number;
  match_type: "keyword" | "semantic" | "hybrid";
}

export interface SearchSummary {
  query: string;
  total_candidates: number;
  results: {
    document_id: number;
    title: string;
    source_path: string;
    snippet: string;
    score: number;
    match_type: string;
  }[];
}

// ---------- BM25 Keyword Search (FTS5) ----------

function bm25Search(
  db: Database.Database,
  query: string,
  limit: number = 10,
): SearchResult[] {
  const stmt = db.prepare(`
    SELECT
      d.id          AS document_id,
      d.source_path,
      d.title,
      d.content,
      d.chunk_index,
      rank           AS score
    FROM documents_fts
    JOIN documents d ON d.id = documents_fts.rowid
    WHERE documents_fts MATCH @query
    ORDER BY rank
    LIMIT @limit
  `);

  const rows = stmt.all({ query: fts5Escape(query), limit }) as Array<{
    document_id: number;
    source_path: string;
    title: string;
    content: string;
    chunk_index: number;
    score: number;
  }>;

  return rows.map((r) => ({
    ...r,
    // FTS5 rank is negative (lower = better), normalize to 0..1
    score: Math.min(1, Math.max(0, 1 + r.score / 10)),
    match_type: "keyword" as const,
  }));
}

/** Escape special FTS5 query characters. */
function fts5Escape(query: string): string {
  // Remove FTS5 operators and wrap each term in quotes for literal matching
  return query
    .replace(/['"]/g, "")
    .split(/\s+/)
    .filter(Boolean)
    .map((term) => `"${term}"`)
    .join(" OR ");
}

// ---------- Vector Similarity Search (sqlite-vec) ----------

async function vectorSearch(
  db: Database.Database,
  query: string,
  limit: number = 10,
): Promise<SearchResult[]> {
  const queryEmbedding = await getEmbedding(query);

  const stmt = db.prepare(`
    SELECT
      de.document_id,
      d.source_path,
      d.title,
      d.content,
      d.chunk_index,
      de.distance
    FROM document_embeddings de
    JOIN documents d ON d.id = de.document_id
    WHERE embedding MATCH @embedding
      AND k = @limit
    ORDER BY de.distance ASC
  `);

  const rows = stmt.all({
    embedding: Buffer.from(queryEmbedding.buffer),
    limit,
  }) as Array<{
    document_id: number;
    source_path: string;
    title: string;
    content: string;
    chunk_index: number;
    distance: number;
  }>;

  return rows.map((r) => ({
    document_id: r.document_id,
    source_path: r.source_path,
    title: r.title,
    content: r.content,
    chunk_index: r.chunk_index,
    // Convert cosine distance to similarity score (0..1)
    score: Math.max(0, 1 - r.distance),
    match_type: "semantic" as const,
  }));
}

// ---------- Hybrid Merge + Local Reranking ----------

const BM25_WEIGHT = 0.4;
const VECTOR_WEIGHT = 0.6;
const TOP_K = 3;

/**
 * Hybrid search: runs BM25 and vector search in parallel,
 * merges scores with weighted combination, returns Top-K results.
 */
export async function hybridSearch(
  db: Database.Database,
  query: string,
  topK: number = TOP_K,
): Promise<SearchResult[]> {
  // Run both search strategies
  const [keywordResults, semanticResults] = await Promise.all([
    Promise.resolve(bm25Search(db, query, topK * 3)),
    vectorSearch(db, query, topK * 3).catch(() => [] as SearchResult[]),
  ]);

  // Merge into a score map keyed by document_id
  const scoreMap = new Map<
    number,
    SearchResult & { bm25: number; vec: number }
  >();

  for (const r of keywordResults) {
    scoreMap.set(r.document_id, {
      ...r,
      bm25: r.score,
      vec: 0,
      match_type: "keyword",
    });
  }

  for (const r of semanticResults) {
    const existing = scoreMap.get(r.document_id);
    if (existing) {
      existing.vec = r.score;
      existing.match_type = "hybrid";
    } else {
      scoreMap.set(r.document_id, {
        ...r,
        bm25: 0,
        vec: r.score,
        match_type: "semantic",
      });
    }
  }

  // Compute weighted hybrid score and rerank
  const merged = Array.from(scoreMap.values()).map((r) => ({
    document_id: r.document_id,
    source_path: r.source_path,
    title: r.title,
    content: r.content,
    chunk_index: r.chunk_index,
    score: r.bm25 * BM25_WEIGHT + r.vec * VECTOR_WEIGHT,
    match_type: r.match_type,
  }));

  // Local reranking: sort by hybrid score, return top K
  merged.sort((a, b) => b.score - a.score);
  return merged.slice(0, topK);
}

/**
 * Build a token-efficient summary for AI agent consumption.
 * Progressive Disclosure: returns snippets, not full text.
 */
export function buildSearchSummary(
  query: string,
  results: SearchResult[],
  totalCandidates: number,
): SearchSummary {
  return {
    query,
    total_candidates: totalCandidates,
    results: results.map((r) => ({
      document_id: r.document_id,
      title: r.title,
      source_path: r.source_path,
      snippet: createSnippet(r.content, query, 200),
      score: Math.round(r.score * 1000) / 1000,
      match_type: r.match_type,
    })),
  };
}

/** Extract a relevant snippet around the first query term match. */
function createSnippet(
  content: string,
  query: string,
  maxLen: number,
): string {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const lower = content.toLowerCase();

  let bestPos = 0;
  for (const term of terms) {
    const idx = lower.indexOf(term);
    if (idx !== -1) {
      bestPos = idx;
      break;
    }
  }

  const start = Math.max(0, bestPos - 40);
  const end = Math.min(content.length, start + maxLen);
  let snippet = content.slice(start, end).trim();

  if (start > 0) snippet = "..." + snippet;
  if (end < content.length) snippet = snippet + "...";

  return snippet;
}
