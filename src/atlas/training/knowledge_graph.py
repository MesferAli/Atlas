"""
Knowledge Graph Extractor for Oracle Fusion Schema

Converts Oracle Fusion ERP schema into a structured Knowledge Graph
for use with GraphGen synthetic data generation.

Based on: https://github.com/InternScience/GraphGen
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class NodeType(str, Enum):
    """Types of nodes in the Knowledge Graph."""
    TABLE = "table"
    VIEW = "view"
    FUNCTION = "function"
    COLUMN = "column"
    FOREIGN_KEY = "foreign_key"
    DOMAIN = "domain"  # HR, Finance, Procurement, etc.


class EdgeType(str, Enum):
    """Types of relationships in the Knowledge Graph."""
    HAS_COLUMN = "has_column"
    REFERENCES = "references"  # FK relationship
    BELONGS_TO = "belongs_to"  # Domain membership
    JOINS_WITH = "joins_with"  # Common join patterns
    AGGREGATES = "aggregates"  # Aggregation relationships


@dataclass
class Node:
    """A node in the Knowledge Graph."""
    id: str
    type: NodeType
    name: str
    name_ar: str  # Arabic name
    description: str
    description_ar: str  # Arabic description
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """An edge (relationship) in the Knowledge Graph."""
    source_id: str
    target_id: str
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)


class OracleKnowledgeGraph:
    """
    Builds a Knowledge Graph from Oracle Fusion Schema.

    This graph captures:
    - Table/View/Function entities
    - Column details and data types
    - Foreign key relationships
    - Business domain groupings (HR, Finance, Procurement)
    - Common join patterns for SQL generation

    The graph is bilingual (Arabic/English) to support
    Atlas's Arabic NL-to-SQL capabilities.
    """

    # Business domain mappings
    DOMAINS = {
        "HR": {
            "prefixes": ["PER_", "PAY_", "CMP_", "HR_"],
            "name_ar": "الموارد البشرية",
            "description": "Human Resources and Payroll",
            "description_ar": "إدارة الموارد البشرية والرواتب"
        },
        "FINANCE": {
            "prefixes": ["GL_", "AP_", "AR_", "FIN_"],
            "name_ar": "المالية",
            "description": "General Ledger, Payables, Receivables",
            "description_ar": "دفتر الأستاذ العام والذمم الدائنة والمدينة"
        },
        "PROCUREMENT": {
            "prefixes": ["PO_", "POZ_"],
            "name_ar": "المشتريات",
            "description": "Purchasing and Supplier Management",
            "description_ar": "إدارة المشتريات والموردين"
        },
        "INVENTORY": {
            "prefixes": ["INV_"],
            "name_ar": "المخزون",
            "description": "Inventory and Stock Management",
            "description_ar": "إدارة المخزون والمستودعات"
        }
    }

    # Arabic translations for common terms
    ARABIC_TERMS = {
        "employee": "موظف",
        "salary": "راتب",
        "department": "قسم",
        "organization": "منظمة",
        "invoice": "فاتورة",
        "payment": "دفعة",
        "supplier": "مورد",
        "vendor": "مورد",
        "customer": "عميل",
        "purchase_order": "أمر شراء",
        "journal": "قيد يومية",
        "balance": "رصيد",
        "inventory": "مخزون",
        "item": "صنف",
        "location": "موقع",
        "job": "وظيفة",
        "grade": "درجة",
        "absence": "غياب",
        "leave": "إجازة",
        "performance": "أداء",
        "headcount": "عدد الموظفين",
    }

    def __init__(self, schema_path: str | Path | None = None):
        """
        Initialize the Knowledge Graph builder.

        Args:
            schema_path: Path to Oracle Fusion schema JSON file
        """
        self.schema_path = Path(schema_path) if schema_path else None
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.schema: list[dict] = []

    def load_schema(self, schema_path: str | Path | None = None) -> None:
        """Load the Oracle Fusion schema from JSON file."""
        path = Path(schema_path) if schema_path else self.schema_path
        if not path:
            raise ValueError("No schema path provided")

        with open(path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def _get_domain(self, table_name: str) -> str | None:
        """Determine which business domain a table belongs to."""
        for domain, config in self.DOMAINS.items():
            for prefix in config["prefixes"]:
                if table_name.startswith(prefix):
                    return domain
        return None

    def _translate_name(self, name: str) -> str:
        """Generate Arabic translation for a table/column name."""
        # Convert from SNAKE_CASE to readable format
        words = name.lower().replace("_", " ").split()

        # Translate known terms
        translated = []
        for word in words:
            if word in self.ARABIC_TERMS:
                translated.append(self.ARABIC_TERMS[word])
            else:
                translated.append(word)

        return " ".join(translated)

    def _parse_column(self, col_str: str) -> dict:
        """Parse column string like 'PERSON_ID (PK)' into structured data."""
        # Match patterns like "COLUMN_NAME (PK)" or "COLUMN_NAME (FK)"
        match = re.match(r"(\w+)\s*(?:\(([^)]+)\))?", col_str)
        if not match:
            return {"name": col_str, "is_pk": False, "is_fk": False}

        name = match.group(1)
        annotation = match.group(2) or ""

        return {
            "name": name,
            "is_pk": "PK" in annotation,
            "is_fk": "FK" in annotation,
            "annotation": annotation
        }

    def _extract_fk_reference(self, col_info: dict, table_name: str) -> str | None:
        """Infer the referenced table from FK column name."""
        col_name = col_info["name"]

        # Common FK patterns
        fk_mappings = {
            "PERSON_ID": "PER_ALL_PEOPLE_F",
            "ASSIGNMENT_ID": "PER_ALL_ASSIGNMENTS_M",
            "VENDOR_ID": "POZ_SUPPLIERS",
            "CUSTOMER_ID": "AR_CUSTOMERS",
            "JE_HEADER_ID": "GL_JE_HEADERS",
            "PO_HEADER_ID": "PO_HEADERS_ALL",
            "INVENTORY_ITEM_ID": "INV_ITEM_MASTER",
            "LOCATION_ID": "HR_LOCATIONS_ALL",
            "JOB_ID": "PER_JOBS_F",
            "GRADE_ID": "PER_GRADES_F",
        }

        return fk_mappings.get(col_name)

    def build_graph(self) -> None:
        """Build the Knowledge Graph from the loaded schema."""
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        # Create domain nodes
        for domain, config in self.DOMAINS.items():
            node = Node(
                id=f"domain_{domain}",
                type=NodeType.DOMAIN,
                name=domain,
                name_ar=config["name_ar"],
                description=config["description"],
                description_ar=config["description_ar"],
            )
            self.nodes[node.id] = node

        # Process each schema object
        for obj in self.schema:
            self._process_schema_object(obj)

        # Infer join patterns
        self._infer_join_patterns()

    def _process_schema_object(self, obj: dict) -> None:
        """Process a single schema object (table/view/function)."""
        obj_type = obj.get("object_type", "TABLE").upper()
        name = obj["name"]
        description = obj.get("description", "")

        # Determine node type
        if obj_type == "TABLE":
            node_type = NodeType.TABLE
        elif obj_type == "VIEW":
            node_type = NodeType.VIEW
        elif obj_type == "FUNCTION":
            node_type = NodeType.FUNCTION
        else:
            node_type = NodeType.TABLE

        # Create main node
        node = Node(
            id=f"{node_type.value}_{name}",
            type=node_type,
            name=name,
            name_ar=self._translate_name(name),
            description=description,
            description_ar=self._translate_name(description),
            properties={
                "classification": obj.get("security_metadata", {}).get("classification", "INTERNAL"),
                "min_role": obj.get("security_metadata", {}).get("min_required_role", ""),
            }
        )
        self.nodes[node.id] = node

        # Link to domain
        domain = self._get_domain(name)
        if domain:
            self.edges.append(Edge(
                source_id=node.id,
                target_id=f"domain_{domain}",
                type=EdgeType.BELONGS_TO,
            ))

        # Process columns
        columns = obj.get("columns", [])
        for col_str in columns:
            col_info = self._parse_column(col_str)
            col_node = Node(
                id=f"column_{name}_{col_info['name']}",
                type=NodeType.COLUMN,
                name=col_info["name"],
                name_ar=self._translate_name(col_info["name"]),
                description=f"Column in {name}",
                description_ar=f"عمود في {self._translate_name(name)}",
                properties={
                    "is_pk": col_info["is_pk"],
                    "is_fk": col_info["is_fk"],
                    "annotation": col_info.get("annotation", ""),
                }
            )
            self.nodes[col_node.id] = col_node

            # Link column to table
            self.edges.append(Edge(
                source_id=node.id,
                target_id=col_node.id,
                type=EdgeType.HAS_COLUMN,
            ))

            # Handle FK relationships
            if col_info["is_fk"]:
                ref_table = self._extract_fk_reference(col_info, name)
                if ref_table:
                    self.edges.append(Edge(
                        source_id=node.id,
                        target_id=f"table_{ref_table}",
                        type=EdgeType.REFERENCES,
                        properties={"fk_column": col_info["name"]},
                    ))

    def _infer_join_patterns(self) -> None:
        """Infer common join patterns from FK relationships."""
        # Find all FK edges
        fk_edges = [e for e in self.edges if e.type == EdgeType.REFERENCES]

        # Create JOIN edges for common patterns
        join_patterns = [
            # HR Joins
            ("table_PER_ALL_PEOPLE_F", "table_PER_ALL_ASSIGNMENTS_M", "PERSON_ID"),
            ("table_PER_ALL_ASSIGNMENTS_M", "table_CMP_ASG_SALARY", "ASSIGNMENT_ID"),
            ("table_PER_ALL_PEOPLE_F", "table_PER_ABSENCE_ENTRIES", "PERSON_ID"),
            ("table_PER_ALL_PEOPLE_F", "table_PER_PERFORMANCE_RATINGS", "PERSON_ID"),
            # Finance Joins
            ("table_GL_JE_HEADERS", "table_GL_JE_LINES", "JE_HEADER_ID"),
            ("table_AP_INVOICES_ALL", "table_POZ_SUPPLIERS", "VENDOR_ID"),
            ("table_AP_PAYMENTS_ALL", "table_POZ_SUPPLIERS", "VENDOR_ID"),
            ("table_AR_INVOICES", "table_AR_CUSTOMERS", "CUSTOMER_ID"),
            # Procurement Joins
            ("table_PO_HEADERS_ALL", "table_PO_LINES_ALL", "PO_HEADER_ID"),
            ("table_PO_HEADERS_ALL", "table_POZ_SUPPLIERS", "VENDOR_ID"),
            ("table_POZ_SUPPLIERS", "table_POZ_SUPPLIER_SITES", "VENDOR_ID"),
        ]

        for source, target, join_col in join_patterns:
            if source in self.nodes and target in self.nodes:
                self.edges.append(Edge(
                    source_id=source,
                    target_id=target,
                    type=EdgeType.JOINS_WITH,
                    properties={"join_column": join_col},
                ))

    def to_dict(self) -> dict:
        """Export the Knowledge Graph as a dictionary."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "name_ar": n.name_ar,
                    "description": n.description,
                    "description_ar": n.description_ar,
                    "properties": n.properties,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.type.value,
                    "properties": e.properties,
                }
                for e in self.edges
            ],
            "metadata": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "domains": list(self.DOMAINS.keys()),
            }
        }

    def to_json(self, output_path: str | Path) -> None:
        """Export the Knowledge Graph to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def get_tables_by_domain(self, domain: str) -> list[Node]:
        """Get all tables belonging to a specific domain."""
        domain_id = f"domain_{domain}"
        table_ids = [
            e.source_id for e in self.edges
            if e.target_id == domain_id and e.type == EdgeType.BELONGS_TO
        ]
        return [self.nodes[tid] for tid in table_ids if tid in self.nodes]

    def get_related_tables(self, table_name: str) -> list[tuple[Node, str]]:
        """Get all tables related to the given table via FK or JOIN."""
        table_id = f"table_{table_name}"
        related = []

        for edge in self.edges:
            if edge.type in (EdgeType.REFERENCES, EdgeType.JOINS_WITH):
                if edge.source_id == table_id and edge.target_id in self.nodes:
                    related.append((
                        self.nodes[edge.target_id],
                        edge.properties.get("join_column", "")
                    ))
                elif edge.target_id == table_id and edge.source_id in self.nodes:
                    related.append((
                        self.nodes[edge.source_id],
                        edge.properties.get("join_column", "")
                    ))

        return related

    def get_graph_stats(self) -> dict:
        """Get statistics about the Knowledge Graph."""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.type.value] = node_types.get(node.type.value, 0) + 1

        edge_types = {}
        for edge in self.edges:
            edge_types[edge.type.value] = edge_types.get(edge.type.value, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "domains": list(self.DOMAINS.keys()),
        }


def build_oracle_knowledge_graph(
    schema_path: str = "data/oracle_fusion_schema.json",
    output_path: str | None = None,
) -> OracleKnowledgeGraph:
    """
    Convenience function to build and optionally export the Knowledge Graph.

    Args:
        schema_path: Path to the Oracle Fusion schema JSON
        output_path: Optional path to export the graph JSON

    Returns:
        OracleKnowledgeGraph instance
    """
    kg = OracleKnowledgeGraph(schema_path)
    kg.load_schema()
    kg.build_graph()

    if output_path:
        kg.to_json(output_path)
        print(f"Knowledge Graph exported to: {output_path}")

    stats = kg.get_graph_stats()
    print(f"Knowledge Graph built: {stats['total_nodes']} nodes, {stats['total_edges']} edges")

    return kg
