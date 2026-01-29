/**
 * Atlas MCP — Local Embedding Engine via Ollama
 *
 * Fetches embeddings from a local Ollama instance running nomic-embed-text.
 * Privacy-first: no data leaves the local machine.
 */

const OLLAMA_BASE = process.env.OLLAMA_BASE_URL ?? "http://127.0.0.1:11434";
const EMBED_MODEL = process.env.ATLAS_EMBED_MODEL ?? "nomic-embed-text";

export interface EmbedResponse {
  embedding: number[];
}

/**
 * Get embedding vector for a single text input.
 * Uses Ollama's /api/embeddings endpoint.
 */
export async function getEmbedding(text: string): Promise<Float32Array> {
  const res = await fetch(`${OLLAMA_BASE}/api/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: EMBED_MODEL, prompt: text }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(
      `Ollama embedding failed (${res.status}): ${body.slice(0, 200)}`,
    );
  }

  const data = (await res.json()) as EmbedResponse;
  return new Float32Array(data.embedding);
}

/**
 * Get embeddings for multiple texts in sequence.
 * Ollama doesn't natively batch, so we call one at a time
 * but reuse the connection.
 */
export async function getEmbeddings(
  texts: string[],
): Promise<Float32Array[]> {
  const results: Float32Array[] = [];
  for (const text of texts) {
    results.push(await getEmbedding(text));
  }
  return results;
}

/** Check if Ollama is reachable and the embed model is available. */
export async function checkOllamaHealth(): Promise<{
  ok: boolean;
  error?: string;
}> {
  try {
    const res = await fetch(`${OLLAMA_BASE}/api/tags`);
    if (!res.ok) {
      return { ok: false, error: `Ollama returned ${res.status}` };
    }
    const data = (await res.json()) as { models?: { name: string }[] };
    const models = data.models?.map((m) => m.name) ?? [];
    const hasModel = models.some((n) => n.startsWith(EMBED_MODEL));
    if (!hasModel) {
      return {
        ok: false,
        error: `Model '${EMBED_MODEL}' not found. Run: ollama pull ${EMBED_MODEL}`,
      };
    }
    return { ok: true };
  } catch (e) {
    return {
      ok: false,
      error: `Cannot reach Ollama at ${OLLAMA_BASE}: ${(e as Error).message}`,
    };
  }
}
