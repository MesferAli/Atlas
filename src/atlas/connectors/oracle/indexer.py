"""Oracle Schema RAG Engine - Indexes table metadata for semantic search."""

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from .connector import OracleConnector


@dataclass
class TableMetadata:
    """Metadata for a database table."""

    table_name: str
    owner: str
    comments: str | None
    column_count: int


class OracleSchemaIndexer:
    """
    Indexes Oracle schema metadata into Qdrant for semantic search.

    Uses sentence-transformers to embed table comments and column descriptions,
    storing them in a local Qdrant instance for RAG-based query routing.
    """

    COLLECTION_NAME = "oracle_schema"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(
        self,
        connector: OracleConnector,
        qdrant_path: str = "./qdrant_data",
    ) -> None:
        """
        Initialize the schema indexer.

        Args:
            connector: OracleConnector instance for database access
            qdrant_path: Local path for Qdrant storage
        """
        self._connector = connector
        self._qdrant = QdrantClient(path=qdrant_path)
        self._embedder = SentenceTransformer(self.EMBEDDING_MODEL)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        collections = self._qdrant.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)

        if not exists:
            self._qdrant.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    async def fetch_table_metadata(self, owner: str | None = None) -> list[TableMetadata]:
        """
        Fetch table metadata from Oracle data dictionary.

        Args:
            owner: Optional schema owner to filter tables

        Returns:
            List of TableMetadata objects
        """
        sql = """
            SELECT
                t.TABLE_NAME,
                t.OWNER,
                c.COMMENTS,
                (SELECT COUNT(*) FROM ALL_TAB_COLUMNS col
                 WHERE col.TABLE_NAME = t.TABLE_NAME AND col.OWNER = t.OWNER) AS COLUMN_COUNT
            FROM ALL_TABLES t
            LEFT JOIN ALL_TAB_COMMENTS c
                ON t.TABLE_NAME = c.TABLE_NAME AND t.OWNER = c.OWNER
            WHERE (:owner IS NULL OR t.OWNER = UPPER(:owner))
            ORDER BY t.OWNER, t.TABLE_NAME
        """

        rows = await self._connector.execute_query(sql, {"owner": owner})

        return [
            TableMetadata(
                table_name=row["TABLE_NAME"],
                owner=row["OWNER"],
                comments=row["COMMENTS"],
                column_count=row["COLUMN_COUNT"],
            )
            for row in rows
        ]

    def _build_document(self, table: TableMetadata) -> str:
        """Build a searchable document from table metadata."""
        parts = [f"Table: {table.owner}.{table.table_name}"]

        if table.comments:
            parts.append(f"Description: {table.comments}")

        parts.append(f"Columns: {table.column_count}")

        return " | ".join(parts)

    async def index_schema(self, owner: str | None = None) -> int:
        """
        Index all table metadata into Qdrant.

        Args:
            owner: Optional schema owner to filter tables

        Returns:
            Number of tables indexed
        """
        tables = await self.fetch_table_metadata(owner)

        if not tables:
            return 0

        # Build documents and embeddings
        documents = [self._build_document(t) for t in tables]
        embeddings = self._embedder.encode(documents)

        # Create Qdrant points
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=embedding.tolist(),
                payload={
                    "table_name": table.table_name,
                    "owner": table.owner,
                    "comments": table.comments,
                    "column_count": table.column_count,
                    "document": doc,
                },
            )
            for table, embedding, doc in zip(tables, embeddings, documents)
        ]

        # Upsert to Qdrant
        self._qdrant.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
        )

        return len(points)

    def search_tables(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for relevant tables using semantic similarity.

        Args:
            query: Natural language query
            limit: Maximum number of results

        Returns:
            List of matching table metadata with scores
        """
        query_embedding = self._embedder.encode(query)

        results = self._qdrant.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding.tolist(),
            limit=limit,
        )

        return [
            {
                "table_name": r.payload["table_name"],
                "owner": r.payload["owner"],
                "comments": r.payload["comments"],
                "score": r.score,
            }
            for r in results
        ]

    def clear_index(self) -> None:
        """Clear all indexed data."""
        self._qdrant.delete_collection(self.COLLECTION_NAME)
        self._ensure_collection()
