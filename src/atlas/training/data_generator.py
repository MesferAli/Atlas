"""
Training Data Generator for Atlas NL-to-SQL

Generates synthetic bilingual (Arabic/English) training data
for fine-tuning LLMs on Oracle Fusion ERP queries.

Based on GraphGen methodology:
https://github.com/InternScience/GraphGen
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.training.knowledge_graph import (
    EdgeType,
    NodeType,
    OracleKnowledgeGraph,
)


@dataclass
class TrainingExample:
    """A single training example for NL-to-SQL."""
    question_en: str
    question_ar: str
    sql: str
    tables_used: list[str]
    complexity: str  # simple, medium, complex
    domain: str  # HR, FINANCE, PROCUREMENT, INVENTORY
    metadata: dict[str, Any]


class TrainingDataGenerator:
    """
    Generates synthetic training data from Oracle Knowledge Graph.

    Uses template-based generation with variations to create
    diverse NL-to-SQL training examples in both Arabic and English.
    """

    # Question templates (English)
    TEMPLATES_EN = {
        "select_all": [
            "Show me all {table_desc}",
            "List all {table_desc}",
            "Get all records from {table_name}",
            "Display all {table_desc}",
            "Retrieve all {table_desc}",
        ],
        "select_columns": [
            "Show me the {columns} from {table_desc}",
            "Get {columns} for all {table_desc}",
            "List {columns} from {table_name}",
            "What are the {columns} in {table_name}?",
        ],
        "count": [
            "How many {table_desc} are there?",
            "Count all {table_desc}",
            "What is the total number of {table_desc}?",
            "Give me the count of {table_desc}",
        ],
        "filter_status": [
            "Show me all {table_desc} where status is {status}",
            "List {table_desc} with status {status}",
            "Get all {status} {table_desc}",
            "Find {table_desc} that are {status}",
        ],
        "aggregate_sum": [
            "What is the total {amount_col} for all {table_desc}?",
            "Calculate the sum of {amount_col} in {table_name}",
            "Show me the total {amount_col}",
        ],
        "aggregate_avg": [
            "What is the average {amount_col} for {table_desc}?",
            "Calculate the average {amount_col}",
            "Show me the mean {amount_col} in {table_name}",
        ],
        "top_n": [
            "Show me the top {n} {table_desc} by {order_col}",
            "List the {n} highest {order_col} in {table_name}",
            "Get top {n} {table_desc} ordered by {order_col}",
        ],
        "join_two": [
            "Show me {table1_desc} with their {table2_desc}",
            "List {table1_desc} and related {table2_desc}",
            "Get {columns} from {table1_name} joined with {table2_name}",
        ],
        "date_range": [
            "Show me {table_desc} from {start_date} to {end_date}",
            "List {table_desc} between {start_date} and {end_date}",
            "Get {table_desc} for the period {start_date} - {end_date}",
        ],
        "group_by": [
            "Show me {table_desc} grouped by {group_col}",
            "List {agg_func} of {amount_col} by {group_col}",
            "Summarize {table_name} by {group_col}",
        ],
    }

    # Question templates (Arabic)
    TEMPLATES_AR = {
        "select_all": [
            "اعرض لي جميع {table_desc}",
            "قائمة بجميع {table_desc}",
            "استرجع جميع السجلات من {table_name}",
            "أظهر كل {table_desc}",
            "جلب جميع {table_desc}",
        ],
        "select_columns": [
            "اعرض لي {columns} من {table_desc}",
            "احصل على {columns} لجميع {table_desc}",
            "قائمة {columns} من {table_name}",
            "ما هي {columns} في {table_name}؟",
        ],
        "count": [
            "كم عدد {table_desc}؟",
            "عد جميع {table_desc}",
            "ما هو إجمالي عدد {table_desc}؟",
            "أعطني عدد {table_desc}",
        ],
        "filter_status": [
            "اعرض لي جميع {table_desc} حيث الحالة {status}",
            "قائمة {table_desc} بحالة {status}",
            "احصل على جميع {table_desc} التي حالتها {status}",
            "ابحث عن {table_desc} التي هي {status}",
        ],
        "aggregate_sum": [
            "ما هو إجمالي {amount_col} لجميع {table_desc}؟",
            "احسب مجموع {amount_col} في {table_name}",
            "اعرض لي إجمالي {amount_col}",
        ],
        "aggregate_avg": [
            "ما هو متوسط {amount_col} لـ {table_desc}؟",
            "احسب متوسط {amount_col}",
            "اعرض لي معدل {amount_col} في {table_name}",
        ],
        "top_n": [
            "اعرض لي أعلى {n} {table_desc} حسب {order_col}",
            "قائمة بأعلى {n} {order_col} في {table_name}",
            "احصل على أعلى {n} {table_desc} مرتبة حسب {order_col}",
        ],
        "join_two": [
            "اعرض لي {table1_desc} مع {table2_desc} الخاصة بهم",
            "قائمة {table1_desc} و {table2_desc} المرتبطة",
            "احصل على {columns} من {table1_name} مع {table2_name}",
        ],
        "date_range": [
            "اعرض لي {table_desc} من {start_date} إلى {end_date}",
            "قائمة {table_desc} بين {start_date} و {end_date}",
            "احصل على {table_desc} للفترة {start_date} - {end_date}",
        ],
        "group_by": [
            "اعرض لي {table_desc} مجمعة حسب {group_col}",
            "قائمة {agg_func} لـ {amount_col} حسب {group_col}",
            "لخص {table_name} حسب {group_col}",
        ],
    }

    # Table descriptions (English/Arabic)
    TABLE_DESCRIPTIONS = {
        "PER_ALL_PEOPLE_F": ("employees", "الموظفين"),
        "PER_ALL_ASSIGNMENTS_M": ("employee assignments", "تعيينات الموظفين"),
        "CMP_ASG_SALARY": ("salary records", "سجلات الرواتب"),
        "PAY_PAYROLL_RELATIONS": ("payroll relations", "علاقات الرواتب"),
        "PO_HEADERS_ALL": ("purchase orders", "أوامر الشراء"),
        "PO_LINES_ALL": ("purchase order lines", "بنود أوامر الشراء"),
        "AP_INVOICES_ALL": ("supplier invoices", "فواتير الموردين"),
        "AP_PAYMENTS_ALL": ("payments", "الدفعات"),
        "AR_CUSTOMERS": ("customers", "العملاء"),
        "AR_INVOICES": ("customer invoices", "فواتير العملاء"),
        "GL_JE_HEADERS": ("journal entries", "القيود اليومية"),
        "GL_JE_LINES": ("journal lines", "سطور القيود"),
        "GL_BALANCES": ("account balances", "أرصدة الحسابات"),
        "POZ_SUPPLIERS": ("suppliers", "الموردين"),
        "POZ_SUPPLIER_SITES": ("supplier sites", "مواقع الموردين"),
        "HR_LOCATIONS_ALL": ("locations", "المواقع"),
        "PER_JOBS_F": ("jobs", "الوظائف"),
        "PER_GRADES_F": ("grades", "الدرجات"),
        "PER_ABSENCE_ENTRIES": ("absences", "الغيابات"),
        "PER_PERFORMANCE_RATINGS": ("performance ratings", "تقييمات الأداء"),
        "INV_ITEM_MASTER": ("inventory items", "أصناف المخزون"),
        "INV_ONHAND_QUANTITIES": ("stock quantities", "كميات المخزون"),
        "FIN_PROFIT_LOSS_V": ("profit and loss", "الأرباح والخسائر"),
        "HR_HEADCOUNT_V": ("headcount", "عدد الموظفين"),
    }

    def __init__(self, knowledge_graph: OracleKnowledgeGraph):
        """
        Initialize the generator with a Knowledge Graph.

        Args:
            knowledge_graph: Pre-built OracleKnowledgeGraph instance
        """
        self.kg = knowledge_graph
        self.examples: list[TrainingExample] = []

    def _get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a table from the Knowledge Graph."""
        columns = []
        table_id = f"table_{table_name}"

        for edge in self.kg.edges:
            if edge.source_id == table_id and edge.type == EdgeType.HAS_COLUMN:
                col_node = self.kg.nodes.get(edge.target_id)
                if col_node:
                    columns.append(col_node.name)

        return columns

    def _get_amount_columns(self, table_name: str) -> list[str]:
        """Get columns that likely contain amounts (for aggregations)."""
        amount_keywords = ["AMOUNT", "SALARY", "PRICE", "COST", "TOTAL", "QUANTITY", "BALANCE", "CR", "DR"]
        columns = self._get_table_columns(table_name)
        return [c for c in columns if any(kw in c.upper() for kw in amount_keywords)]

    def _get_date_columns(self, table_name: str) -> list[str]:
        """Get columns that likely contain dates."""
        date_keywords = ["DATE", "START", "END", "EFFECTIVE", "CREATED", "UPDATED"]
        columns = self._get_table_columns(table_name)
        return [c for c in columns if any(kw in c.upper() for kw in date_keywords)]

    def generate_simple_queries(self, table_name: str, count: int = 10) -> list[TrainingExample]:
        """Generate simple SELECT queries for a table."""
        examples = []
        table_desc = self.TABLE_DESCRIPTIONS.get(table_name, (table_name.lower(), table_name))
        columns = self._get_table_columns(table_name)

        for _ in range(count):
            template_type = random.choice(["select_all", "select_columns", "count"])

            if template_type == "select_all":
                template_en = random.choice(self.TEMPLATES_EN["select_all"])
                template_ar = random.choice(self.TEMPLATES_AR["select_all"])

                question_en = template_en.format(
                    table_desc=table_desc[0],
                    table_name=table_name,
                )
                question_ar = template_ar.format(
                    table_desc=table_desc[1],
                    table_name=table_name,
                )
                sql = f"SELECT * FROM {table_name}"

            elif template_type == "select_columns" and len(columns) >= 2:
                selected_cols = random.sample(columns[:6], min(3, len(columns)))
                cols_str = ", ".join(selected_cols)

                template_en = random.choice(self.TEMPLATES_EN["select_columns"])
                template_ar = random.choice(self.TEMPLATES_AR["select_columns"])

                question_en = template_en.format(
                    columns=cols_str.lower().replace("_", " "),
                    table_desc=table_desc[0],
                    table_name=table_name,
                )
                question_ar = template_ar.format(
                    columns=cols_str,
                    table_desc=table_desc[1],
                    table_name=table_name,
                )
                sql = f"SELECT {cols_str} FROM {table_name}"

            else:  # count
                template_en = random.choice(self.TEMPLATES_EN["count"])
                template_ar = random.choice(self.TEMPLATES_AR["count"])

                question_en = template_en.format(table_desc=table_desc[0])
                question_ar = template_ar.format(table_desc=table_desc[1])
                sql = f"SELECT COUNT(*) FROM {table_name}"

            # Determine domain
            domain = "GENERAL"
            for d, config in self.kg.DOMAINS.items():
                for prefix in config["prefixes"]:
                    if table_name.startswith(prefix):
                        domain = d
                        break

            examples.append(TrainingExample(
                question_en=question_en,
                question_ar=question_ar,
                sql=sql,
                tables_used=[table_name],
                complexity="simple",
                domain=domain,
                metadata={"template_type": template_type},
            ))

        return examples

    def generate_aggregate_queries(self, table_name: str, count: int = 5) -> list[TrainingExample]:
        """Generate aggregation queries (SUM, AVG, COUNT)."""
        examples = []
        table_desc = self.TABLE_DESCRIPTIONS.get(table_name, (table_name.lower(), table_name))
        amount_cols = self._get_amount_columns(table_name)

        if not amount_cols:
            return examples

        for _ in range(count):
            amount_col = random.choice(amount_cols)
            agg_type = random.choice(["sum", "avg"])

            if agg_type == "sum":
                template_en = random.choice(self.TEMPLATES_EN["aggregate_sum"])
                template_ar = random.choice(self.TEMPLATES_AR["aggregate_sum"])
                sql = f"SELECT SUM({amount_col}) FROM {table_name}"
            else:
                template_en = random.choice(self.TEMPLATES_EN["aggregate_avg"])
                template_ar = random.choice(self.TEMPLATES_AR["aggregate_avg"])
                sql = f"SELECT AVG({amount_col}) FROM {table_name}"

            question_en = template_en.format(
                amount_col=amount_col.lower().replace("_", " "),
                table_desc=table_desc[0],
                table_name=table_name,
            )
            question_ar = template_ar.format(
                amount_col=amount_col,
                table_desc=table_desc[1],
                table_name=table_name,
            )

            domain = "GENERAL"
            for d, config in self.kg.DOMAINS.items():
                for prefix in config["prefixes"]:
                    if table_name.startswith(prefix):
                        domain = d
                        break

            examples.append(TrainingExample(
                question_en=question_en,
                question_ar=question_ar,
                sql=sql,
                tables_used=[table_name],
                complexity="medium",
                domain=domain,
                metadata={"template_type": f"aggregate_{agg_type}", "amount_col": amount_col},
            ))

        return examples

    def generate_join_queries(self, count: int = 20) -> list[TrainingExample]:
        """Generate JOIN queries based on FK relationships."""
        examples = []

        # Find all join edges
        join_edges = [e for e in self.kg.edges if e.type == EdgeType.JOINS_WITH]

        for edge in join_edges[:count]:
            source_name = edge.source_id.replace("table_", "")
            target_name = edge.target_id.replace("table_", "")
            join_col = edge.properties.get("join_column", "ID")

            source_desc = self.TABLE_DESCRIPTIONS.get(source_name, (source_name.lower(), source_name))
            target_desc = self.TABLE_DESCRIPTIONS.get(target_name, (target_name.lower(), target_name))

            template_en = random.choice(self.TEMPLATES_EN["join_two"])
            template_ar = random.choice(self.TEMPLATES_AR["join_two"])

            question_en = template_en.format(
                table1_desc=source_desc[0],
                table2_desc=target_desc[0],
                table1_name=source_name,
                table2_name=target_name,
                columns="details",
            )
            question_ar = template_ar.format(
                table1_desc=source_desc[1],
                table2_desc=target_desc[1],
                table1_name=source_name,
                table2_name=target_name,
                columns="التفاصيل",
            )

            sql = f"""SELECT a.*, b.*
FROM {source_name} a
JOIN {target_name} b ON a.{join_col} = b.{join_col}"""

            domain = "GENERAL"
            for d, config in self.kg.DOMAINS.items():
                for prefix in config["prefixes"]:
                    if source_name.startswith(prefix):
                        domain = d
                        break

            examples.append(TrainingExample(
                question_en=question_en,
                question_ar=question_ar,
                sql=sql.strip(),
                tables_used=[source_name, target_name],
                complexity="complex",
                domain=domain,
                metadata={"template_type": "join", "join_column": join_col},
            ))

        return examples

    def generate_top_n_queries(self, table_name: str, count: int = 5) -> list[TrainingExample]:
        """Generate TOP N queries with ORDER BY."""
        examples = []
        table_desc = self.TABLE_DESCRIPTIONS.get(table_name, (table_name.lower(), table_name))
        amount_cols = self._get_amount_columns(table_name)

        if not amount_cols:
            return examples

        for _ in range(count):
            n = random.choice([5, 10, 15, 20])
            order_col = random.choice(amount_cols)

            template_en = random.choice(self.TEMPLATES_EN["top_n"])
            template_ar = random.choice(self.TEMPLATES_AR["top_n"])

            question_en = template_en.format(
                n=n,
                table_desc=table_desc[0],
                order_col=order_col.lower().replace("_", " "),
                table_name=table_name,
            )
            question_ar = template_ar.format(
                n=n,
                table_desc=table_desc[1],
                order_col=order_col,
                table_name=table_name,
            )

            sql = f"SELECT * FROM {table_name} ORDER BY {order_col} DESC FETCH FIRST {n} ROWS ONLY"

            domain = "GENERAL"
            for d, config in self.kg.DOMAINS.items():
                for prefix in config["prefixes"]:
                    if table_name.startswith(prefix):
                        domain = d
                        break

            examples.append(TrainingExample(
                question_en=question_en,
                question_ar=question_ar,
                sql=sql,
                tables_used=[table_name],
                complexity="medium",
                domain=domain,
                metadata={"template_type": "top_n", "n": n, "order_col": order_col},
            ))

        return examples

    def generate_all(
        self,
        simple_per_table: int = 10,
        aggregate_per_table: int = 5,
        top_n_per_table: int = 5,
        join_count: int = 30,
    ) -> list[TrainingExample]:
        """
        Generate a complete training dataset.

        Args:
            simple_per_table: Number of simple queries per table
            aggregate_per_table: Number of aggregate queries per table
            top_n_per_table: Number of TOP N queries per table
            join_count: Number of JOIN queries

        Returns:
            List of all generated training examples
        """
        all_examples = []

        # Get all table nodes
        table_nodes = [n for n in self.kg.nodes.values() if n.type == NodeType.TABLE]

        for table_node in table_nodes:
            table_name = table_node.name

            # Simple queries
            all_examples.extend(self.generate_simple_queries(table_name, simple_per_table))

            # Aggregate queries
            all_examples.extend(self.generate_aggregate_queries(table_name, aggregate_per_table))

            # TOP N queries
            all_examples.extend(self.generate_top_n_queries(table_name, top_n_per_table))

        # JOIN queries
        all_examples.extend(self.generate_join_queries(join_count))

        self.examples = all_examples
        return all_examples

    def to_jsonl(self, output_path: str | Path, format: str = "alpaca") -> None:
        """
        Export training data to JSONL format.

        Args:
            output_path: Path to output file
            format: Output format ('alpaca', 'sharegpt', 'completion')
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for example in self.examples:
                if format == "alpaca":
                    # Alpaca format for fine-tuning
                    record = {
                        "instruction": "أنت خبير في Oracle SQL. اكتب استعلام SQL للسؤال التالي.\nYou are an Oracle SQL expert. Write a SQL query for the following question.",
                        "input": f"Question (EN): {example.question_en}\nQuestion (AR): {example.question_ar}",
                        "output": example.sql,
                    }
                elif format == "sharegpt":
                    # ShareGPT format
                    record = {
                        "conversations": [
                            {"from": "human", "value": f"{example.question_en}\n{example.question_ar}"},
                            {"from": "gpt", "value": example.sql},
                        ]
                    }
                else:  # completion format
                    record = {
                        "prompt": f"Question: {example.question_en}\nسؤال: {example.question_ar}\n\nSQL:",
                        "completion": f" {example.sql}",
                    }

                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"Exported {len(self.examples)} examples to {output_path}")

    def get_stats(self) -> dict:
        """Get statistics about generated data."""
        stats = {
            "total_examples": len(self.examples),
            "by_complexity": {},
            "by_domain": {},
            "by_template": {},
        }

        for ex in self.examples:
            stats["by_complexity"][ex.complexity] = stats["by_complexity"].get(ex.complexity, 0) + 1
            stats["by_domain"][ex.domain] = stats["by_domain"].get(ex.domain, 0) + 1
            template = ex.metadata.get("template_type", "unknown")
            stats["by_template"][template] = stats["by_template"].get(template, 0) + 1

        return stats
