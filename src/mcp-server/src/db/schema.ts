/**
 * Atlas MCP — Database Schema & Initialization
 *
 * Sets up SQLite with:
 *  - documents        : raw document storage
 *  - documents_fts    : FTS5 full-text index for BM25 keyword search
 *  - document_embeddings : sqlite-vec virtual table for 768-dim vector search
 */

import Database from "better-sqlite3";
import * as sqliteVec from "sqlite-vec";
import path from "node:path";

const DEFAULT_DB_PATH = path.resolve(
  import.meta.dir ?? ".",
  "../../../data/atlas_search.db",
);

export const EMBEDDING_DIM = 768; // nomic-embed-text output dimension

export interface DocumentRow {
  id: number;
  source_path: string;
  title: string;
  content: string;
  chunk_index: number;
  metadata_json: string;
  created_at: string;
  updated_at: string;
}

export function openDatabase(dbPath?: string): Database.Database {
  const resolved = dbPath ?? process.env.ATLAS_SEARCH_DB ?? DEFAULT_DB_PATH;
  const db = new Database(resolved);

  // Performance pragmas
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = NORMAL");
  db.pragma("cache_size = -64000"); // 64 MB
  db.pragma("busy_timeout = 5000");

  // Load sqlite-vec extension
  sqliteVec.load(db);

  return db;
}

export function initSchema(db: Database.Database): void {
  db.exec(`
    -- Core document store
    CREATE TABLE IF NOT EXISTS documents (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      source_path  TEXT    NOT NULL,
      title        TEXT    NOT NULL DEFAULT '',
      content      TEXT    NOT NULL,
      chunk_index  INTEGER NOT NULL DEFAULT 0,
      metadata_json TEXT   NOT NULL DEFAULT '{}',
      created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
      updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
      UNIQUE(source_path, chunk_index)
    );

    -- FTS5 full-text index for BM25 keyword search
    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
      title,
      content,
      content='documents',
      content_rowid='id',
      tokenize='porter unicode61'
    );

    -- Triggers to keep FTS in sync
    CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
      INSERT INTO documents_fts(rowid, title, content)
        VALUES (new.id, new.title, new.content);
    END;

    CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
      INSERT INTO documents_fts(documents_fts, rowid, title, content)
        VALUES ('delete', old.id, old.title, old.content);
    END;

    CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
      INSERT INTO documents_fts(documents_fts, rowid, title, content)
        VALUES ('delete', old.id, old.title, old.content);
      INSERT INTO documents_fts(rowid, title, content)
        VALUES (new.id, new.title, new.content);
    END;
  `);

  // sqlite-vec virtual table for vector similarity search (768 dimensions)
  db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS document_embeddings USING vec0(
      document_id INTEGER PRIMARY KEY,
      embedding   float[${EMBEDDING_DIM}]
    );
  `);
}

/** Insert or replace a document chunk and return its id. */
export function upsertDocument(
  db: Database.Database,
  doc: {
    source_path: string;
    title: string;
    content: string;
    chunk_index: number;
    metadata_json?: string;
  },
): number {
  const stmt = db.prepare(`
    INSERT INTO documents (source_path, title, content, chunk_index, metadata_json, updated_at)
    VALUES (@source_path, @title, @content, @chunk_index, @metadata_json, datetime('now'))
    ON CONFLICT(source_path, chunk_index) DO UPDATE SET
      title = excluded.title,
      content = excluded.content,
      metadata_json = excluded.metadata_json,
      updated_at = datetime('now')
    RETURNING id
  `);

  const row = stmt.get({
    source_path: doc.source_path,
    title: doc.title,
    content: doc.content,
    chunk_index: doc.chunk_index,
    metadata_json: doc.metadata_json ?? "{}",
  }) as { id: number };

  return row.id;
}

/** Store a vector embedding for a document. */
export function upsertEmbedding(
  db: Database.Database,
  documentId: number,
  embedding: Float32Array,
): void {
  // Delete existing then insert (vec0 doesn't support ON CONFLICT)
  db.prepare("DELETE FROM document_embeddings WHERE document_id = ?").run(
    documentId,
  );
  db.prepare(
    "INSERT INTO document_embeddings (document_id, embedding) VALUES (?, ?)",
  ).run(documentId, Buffer.from(embedding.buffer));
}
