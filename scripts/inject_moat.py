#!/usr/bin/env python3
"""
Data Moat Injection Script - Ingest Oracle Fusion schema into Qdrant vector store.

This script reads the Oracle Fusion schema JSON and upserts it into Qdrant
with security metadata (min_required_role, classification) for role-based filtering.

Usage:
    # Local mode (file-based Qdrant)
    python scripts/inject_moat.py --qdrant-path ./qdrant_data

    # Server mode (Qdrant server)
    python scripts/inject_moat.py --qdrant-host localhost --qdrant-port 6333

    # Offline mode (no HuggingFace connection required)
    python scripts/inject_moat.py --qdrant-path ./qdrant_data --offline

    # Use local model path
    python scripts/inject_moat.py --model-path /path/to/local/model

Environment Variables:
    ATLAS_SCHEMA_PATH: Path to oracle_fusion_schema.json
    ATLAS_QDRANT_PATH: Path to Qdrant storage directory (local mode)
    ATLAS_QDRANT_HOST: Qdrant server host (server mode)
    ATLAS_QDRANT_PORT: Qdrant server port (server mode)
    ATLAS_MODEL_PATH: Path to local embedding model
    HF_HUB_OFFLINE: Set to 1 to use offline mode
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Configuration
COLLECTION_NAME = "oracle_schema"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
OFFLINE_EMBEDDING_DIM = 256  # Dimension for fallback hash-based embedding


class OfflineEmbedder:
    """
    Fallback embedder using hash-based vectors when HuggingFace is unavailable.
    Uses a combination of character n-grams and word hashing for semantic similarity.
    """

    def __init__(self, dim: int = OFFLINE_EMBEDDING_DIM):
        self.dim = dim
        print(f"  Using offline hash-based embedder (dim={dim})")

    def encode(self, text: str) -> list:
        """Generate a deterministic embedding from text using multiple hash functions."""
        import numpy as np

        text = text.lower().strip()
        vector = np.zeros(self.dim, dtype=np.float32)

        # Word-level hashing
        words = text.split()
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dim
            vector[idx] += 1.0

        # Character trigram hashing for better semantic capture
        for i in range(len(text) - 2):
            trigram = text[i:i+3]
            h = int(hashlib.sha256(trigram.encode()).hexdigest(), 16)
            idx = h % self.dim
            vector[idx] += 0.5

        # Normalize to unit vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()


def load_embedder(model_path: str = None, offline: bool = False):
    """
    Load the embedding model with fallback options.

    Args:
        model_path: Path to local model directory
        offline: If True, use offline hash-based embedder

    Returns:
        Tuple of (embedder, embedding_dimension)
    """
    if offline:
        print("  Offline mode enabled - using hash-based embedder")
        return OfflineEmbedder(OFFLINE_EMBEDDING_DIM), OFFLINE_EMBEDDING_DIM

    # Try loading from local path first
    if model_path and Path(model_path).exists():
        try:
            from sentence_transformers import SentenceTransformer
            print(f"  Loading model from local path: {model_path}")
            return SentenceTransformer(model_path), EMBEDDING_DIM
        except Exception as e:
            print(f"  Warning: Failed to load local model: {e}")

    # Try loading from HuggingFace with offline mode check
    try:
        # Set offline mode if HF_HUB_OFFLINE is set
        if os.getenv("HF_HUB_OFFLINE", "0") == "1":
            print("  HF_HUB_OFFLINE=1, using cached model only")

        from sentence_transformers import SentenceTransformer
        print(f"  Loading model: {EMBEDDING_MODEL}")
        return SentenceTransformer(EMBEDDING_MODEL), EMBEDDING_DIM
    except Exception as e:
        print(f"  Warning: Failed to load transformer model: {e}")
        print("  Falling back to offline hash-based embedder")
        return OfflineEmbedder(OFFLINE_EMBEDDING_DIM), OFFLINE_EMBEDDING_DIM

# Default paths
DEFAULT_SCHEMA_PATH = "/workspace/atlas_erp/data/oracle_fusion_schema.json"
DEFAULT_QDRANT_PATH = "./qdrant_data"
DEFAULT_QDRANT_HOST = "localhost"
DEFAULT_QDRANT_PORT = 6333


def load_schema(schema_path: str) -> list[dict]:
    """Load Oracle Fusion schema from JSON file."""
    path = Path(schema_path)
    if not path.exists():
        # Try local data directory as fallback
        local_path = Path(__file__).parent.parent / "data" / "oracle_fusion_schema.json"
        if local_path.exists():
            path = local_path
            print(f"Using local schema: {path}")
        else:
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, encoding="utf-8") as f:
        schema = json.load(f)

    print(f"Loaded {len(schema)} objects from schema")
    return schema


def build_document(obj: dict) -> str:
    """
    Build a searchable document from a schema object.

    Combines object type, name, description, and columns/parameters
    into a single string for embedding.
    """
    parts = [
        f"Object: {obj['object_type']} {obj['name']}",
        f"Description: {obj['description']}",
    ]

    # Add columns for tables
    if "columns" in obj:
        columns_str = ", ".join(obj["columns"])
        parts.append(f"Columns: {columns_str}")

    # Add parameters for functions
    if "parameters" in obj:
        params_str = ", ".join(obj["parameters"])
        parts.append(f"Parameters: {params_str}")
        if "return_type" in obj:
            parts.append(f"Returns: {obj['return_type']}")

    return " | ".join(parts)


def create_qdrant_collection(client: QdrantClient, embedding_dim: int) -> None:
    """Create or recreate the Qdrant collection."""
    if client.collection_exists(COLLECTION_NAME):
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME} (dim={embedding_dim})")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=embedding_dim,
            distance=Distance.COSINE,
        ),
    )


def inject_schema(
    schema: list[dict],
    client: QdrantClient,
    embedder,
) -> int:
    """
    Inject schema objects into Qdrant with security metadata.

    Args:
        schema: List of schema objects from JSON
        client: Qdrant client
        embedder: SentenceTransformer model

    Returns:
        Number of objects injected
    """
    points = []

    for idx, obj in enumerate(schema):
        # Build searchable document (combine name, description, columns)
        document = build_document(obj)

        # Generate embedding
        embedding = embedder.encode(document)
        if not isinstance(embedding, list):
            embedding = embedding.tolist()

        # Extract security metadata
        security = obj.get("security_metadata", {})

        # Build payload with all metadata for filtering
        payload = {
            "name": obj["name"],
            "type": obj["object_type"],
            "description": obj["description"],
            "document": document,
            # Security metadata for role-based filtering
            "classification": security.get("classification", "INTERNAL"),
            "min_required_role": security.get("min_required_role", "PUBLIC"),
            "access_predicate": security.get("access_predicate", ""),
        }

        # Add columns/parameters if present
        if "columns" in obj:
            payload["columns"] = obj["columns"]
        if "parameters" in obj:
            payload["parameters"] = obj["parameters"]
        if "return_type" in obj:
            payload["return_type"] = obj["return_type"]

        # Create point with integer ID (more compatible)
        point = PointStruct(
            id=idx,
            vector=embedding,
            payload=payload,
        )
        points.append(point)

        classification = security.get("classification", "N/A")
        role = security.get("min_required_role", "N/A")
        print(f"  + {obj['object_type']}: {obj['name']}")
        print(f"    Classification: {classification} | Role: {role}")

    # Upsert all points
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)


def verify_collection(client: QdrantClient, embedder) -> None:
    """Verify the collection was created correctly."""
    info = client.get_collection(COLLECTION_NAME)
    print("\nCollection Stats:")
    print(f"  Points: {info.points_count}")

    # Sample query to verify
    print("\nSample search for 'salary':")
    query_vector = embedder.encode("salary employee payment")
    if not isinstance(query_vector, list):
        query_vector = query_vector.tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3,
    )

    for i, result in enumerate(results.points, 1):
        print(f"  {i}. {result.payload['name']} (score: {result.score:.3f})")
        print(f"     Classification: {result.payload['classification']}")
        print(f"     Required Role: {result.payload['min_required_role']}")


def main():
    parser = argparse.ArgumentParser(
        description="Inject Oracle Fusion schema into Qdrant vector store"
    )
    parser.add_argument(
        "--schema-path",
        default=os.getenv("ATLAS_SCHEMA_PATH", DEFAULT_SCHEMA_PATH),
        help="Path to oracle_fusion_schema.json",
    )
    parser.add_argument(
        "--qdrant-path",
        default=os.getenv("ATLAS_QDRANT_PATH"),
        help="Path to Qdrant storage directory (local mode)",
    )
    parser.add_argument(
        "--qdrant-host",
        default=os.getenv("ATLAS_QDRANT_HOST"),
        help="Qdrant server host (server mode)",
    )
    parser.add_argument(
        "--qdrant-port",
        type=int,
        default=int(os.getenv("ATLAS_QDRANT_PORT", DEFAULT_QDRANT_PORT)),
        help="Qdrant server port (server mode)",
    )
    parser.add_argument(
        "--model-path",
        default=os.getenv("ATLAS_MODEL_PATH"),
        help="Path to local embedding model directory",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=os.getenv("HF_HUB_OFFLINE", "0") == "1",
        help="Use offline hash-based embedder (no HuggingFace connection)",
    )
    args = parser.parse_args()

    # Determine connection mode
    if args.qdrant_host:
        mode = "server"
        qdrant_info = f"{args.qdrant_host}:{args.qdrant_port}"
    elif args.qdrant_path:
        mode = "local"
        qdrant_info = args.qdrant_path
    else:
        # Default to local mode
        mode = "local"
        args.qdrant_path = DEFAULT_QDRANT_PATH
        qdrant_info = args.qdrant_path

    # Determine embedding mode
    if args.offline:
        embed_mode = "OFFLINE (hash-based)"
    elif args.model_path:
        embed_mode = f"LOCAL ({args.model_path})"
    else:
        embed_mode = f"ONLINE ({EMBEDDING_MODEL})"

    print("=" * 60)
    print("Data Moat Injection - Oracle Fusion Schema to Qdrant")
    print("=" * 60)
    print(f"Schema Path: {args.schema_path}")
    print(f"Qdrant Mode: {mode.upper()}")
    print(f"Qdrant:      {qdrant_info}")
    print(f"Collection:  {COLLECTION_NAME}")
    print(f"Embedding:   {embed_mode}")
    print("=" * 60)

    # Load schema
    print("\n[1/5] Loading schema...")
    schema = load_schema(args.schema_path)

    # Load embedding model
    print("\n[2/5] Loading embedding model...")
    embedder, embedding_dim = load_embedder(args.model_path, args.offline)

    # Initialize Qdrant
    print("\n[3/5] Initializing Qdrant...")
    if mode == "server":
        client = QdrantClient(host=args.qdrant_host, port=args.qdrant_port)
    else:
        client = QdrantClient(path=args.qdrant_path)

    # Create collection
    print("\n[4/5] Creating collection...")
    create_qdrant_collection(client, embedding_dim)

    # Inject schema
    print("\n[5/5] Injecting schema into Qdrant...")
    count = inject_schema(schema, client, embedder)

    print(f"\nSuccessfully injected {count} objects into Qdrant!")

    # Verify
    verify_collection(client, embedder)

    print("\n" + "=" * 60)
    print("Data Moat injection complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
