#!/usr/bin/env python3
"""
Data Moat Injection Script - Ingest Oracle Fusion schema into Qdrant vector store.

This script reads the Oracle Fusion schema JSON and upserts it into Qdrant
with security metadata (min_required_role, classification) for role-based filtering.

Usage:
    python scripts/inject_moat.py [--schema-path PATH] [--qdrant-path PATH]

Environment Variables:
    ATLAS_SCHEMA_PATH: Path to oracle_fusion_schema.json
    ATLAS_QDRANT_PATH: Path to Qdrant storage directory
"""

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer


# Configuration
COLLECTION_NAME = "oracle_schema"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Default paths
DEFAULT_SCHEMA_PATH = "/workspace/atlas_erp/data/oracle_fusion_schema.json"
DEFAULT_QDRANT_PATH = "./qdrant_data"


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


def create_qdrant_collection(client: QdrantClient) -> None:
    """Create or recreate the Qdrant collection."""
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if exists:
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )


def inject_schema(
    schema: list[dict],
    client: QdrantClient,
    embedder: SentenceTransformer,
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

    for obj in schema:
        # Build searchable document
        document = build_document(obj)

        # Generate embedding
        embedding = embedder.encode(document)

        # Extract security metadata
        security = obj.get("security_metadata", {})

        # Build payload with all metadata for filtering
        payload = {
            "object_type": obj["object_type"],
            "name": obj["name"],
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

        # Create point
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding.tolist(),
            payload=payload,
        )
        points.append(point)

        print(f"  + {obj['object_type']}: {obj['name']} [{security.get('classification', 'N/A')}]")

    # Upsert all points
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)


def verify_collection(client: QdrantClient) -> None:
    """Verify the collection was created correctly."""
    info = client.get_collection(COLLECTION_NAME)
    print(f"\nCollection Stats:")
    print(f"  Points: {info.points_count}")

    # Sample query to verify
    print(f"\nSample search for 'salary':")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    query_vector = embedder.encode("salary employee payment").tolist()

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
        default=os.getenv("ATLAS_QDRANT_PATH", DEFAULT_QDRANT_PATH),
        help="Path to Qdrant storage directory",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Data Moat Injection - Oracle Fusion Schema to Qdrant")
    print("=" * 60)
    print(f"Schema Path: {args.schema_path}")
    print(f"Qdrant Path: {args.qdrant_path}")
    print(f"Collection:  {COLLECTION_NAME}")
    print(f"Model:       {EMBEDDING_MODEL}")
    print("=" * 60)

    # Load schema
    print("\n[1/4] Loading schema...")
    schema = load_schema(args.schema_path)

    # Initialize Qdrant
    print("\n[2/4] Initializing Qdrant...")
    client = QdrantClient(path=args.qdrant_path)

    # Create collection
    print("\n[3/4] Creating collection...")
    create_qdrant_collection(client)

    # Load embedding model
    print("\n[4/4] Injecting schema into Qdrant...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    count = inject_schema(schema, client, embedder)

    print(f"\nSuccessfully injected {count} objects into Qdrant!")

    # Verify
    verify_collection(client)

    print("\n" + "=" * 60)
    print("Data Moat injection complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
