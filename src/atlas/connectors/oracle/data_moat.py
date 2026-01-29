"""
Data Moat - Role-based schema filtering for Oracle Fusion tables.

SECURITY: Enforces data classification and RBAC at the schema search level.
Tables are filtered based on user role before being returned to the NL-to-SQL agent.
"""

import json
from pathlib import Path
from typing import Any

from atlas.api.security.models import UserRole

# Classification hierarchy (higher index = more restricted)
CLASSIFICATION_LEVELS = ["PUBLIC", "INTERNAL", "RESTRICTED", "SECRET", "TOP_SECRET"]

# Role-to-max-classification mapping
ROLE_CLEARANCE: dict[str, int] = {
    UserRole.VIEWER.value: 1,    # PUBLIC, INTERNAL
    UserRole.ANALYST.value: 2,   # up to RESTRICTED
    UserRole.SERVICE.value: 3,   # up to SECRET
    UserRole.ADMIN.value: 4,     # all levels
}


def load_schema_metadata(
    schema_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Load Oracle Fusion schema with security metadata.

    Args:
        schema_path: Path to oracle_fusion_schema.json.
                     Defaults to data/oracle_fusion_schema.json.

    Returns:
        List of schema objects with security metadata.
    """
    if schema_path is None:
        schema_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "data"
            / "oracle_fusion_schema.json"
        )
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        return []

    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def get_classification_level(classification: str) -> int:
    """Convert classification string to numeric level."""
    classification = classification.upper()
    if classification in CLASSIFICATION_LEVELS:
        return CLASSIFICATION_LEVELS.index(classification)
    return 1  # Default to INTERNAL


def _resolve_classification(
    table: dict[str, Any],
    schema_lookup: dict[str, str] | None,
) -> str:
    """Resolve the classification for a table dict.

    Checks three sources in order:
    1. Inline ``security_metadata.classification`` on the dict itself
    2. Inline ``classification`` key (Qdrant payload format)
    3. Schema JSON lookup by ``table_name`` or ``name``

    Falls back to INTERNAL if nothing matches.
    """
    # Source 1: nested security_metadata (schema JSON format)
    security = table.get("security_metadata", {})
    if security.get("classification"):
        return security["classification"]

    # Source 2: flat classification key (Qdrant payload format)
    if table.get("classification"):
        return table["classification"]

    # Source 3: lookup from loaded schema JSON
    if schema_lookup:
        name = (
            table.get("table_name")
            or table.get("name")
            or ""
        ).upper()
        if name in schema_lookup:
            return schema_lookup[name]

    return "INTERNAL"


def filter_tables_by_role(
    tables: list[dict[str, Any]],
    user_role: str,
) -> list[dict[str, Any]]:
    """
    Filter schema tables based on user role and classification level.

    SECURITY: This is a critical access control point. Tables with
    classification above the user's clearance are excluded from
    search results, preventing the NL-to-SQL agent from even
    seeing restricted schemas.

    The function handles tables from multiple sources:
    - Schema JSON objects (have ``security_metadata.classification``)
    - Qdrant search results (have flat ``classification`` key)
    - Indexer search results (have ``table_name`` only — looked up
      against the schema JSON on disk)

    Args:
        tables: List of table metadata dicts (from schema JSON or search results)
        user_role: The role of the requesting user

    Returns:
        Filtered list containing only tables the user may access
    """
    max_level = ROLE_CLEARANCE.get(user_role, 0)

    # Build a lookup table from schema JSON for tables that lack
    # inline classification (e.g. results from OracleSchemaIndexer)
    schema_lookup: dict[str, str] | None = None
    needs_lookup = any(
        not t.get("security_metadata", {}).get("classification")
        and not t.get("classification")
        for t in tables
    )
    if needs_lookup:
        schema = load_schema_metadata()
        schema_lookup = {
            obj["name"].upper(): obj.get("security_metadata", {}).get(
                "classification", "INTERNAL"
            )
            for obj in schema
            if "name" in obj
        }

    filtered = []
    for table in tables:
        classification = _resolve_classification(table, schema_lookup)
        table_level = get_classification_level(classification)

        if table_level <= max_level:
            filtered.append(table)

    return filtered


def get_table_classification(table_name: str, schema: list[dict[str, Any]] | None = None) -> str:
    """
    Look up the classification level for a specific table.

    Args:
        table_name: Name of the Oracle Fusion table
        schema: Optional pre-loaded schema (loads from disk if None)

    Returns:
        Classification string (e.g. "SECRET") or "INTERNAL" if not found
    """
    if schema is None:
        schema = load_schema_metadata()

    for obj in schema:
        if obj.get("name", "").upper() == table_name.upper():
            security = obj.get("security_metadata", {})
            return security.get("classification", "INTERNAL")

    return "INTERNAL"
