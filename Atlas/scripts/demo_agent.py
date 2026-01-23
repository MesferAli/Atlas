#!/usr/bin/env python3
"""Demo script for the Oracle SQL RAG Agent.

This script simulates a full run of the SQL RAG Agent pipeline.
Since we don't have a real Oracle database, it uses mocks to demonstrate the flow.
"""

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from atlas.agent.sql_agent import AgentResponse, MockLLM, OracleSQLAgent
from atlas.connectors.oracle.connector import OracleConnector
from atlas.connectors.oracle.indexer import OracleSchemaIndexer


def create_mock_connector() -> OracleConnector:
    """Create a mock OracleConnector that returns sample data."""
    connector = MagicMock(spec=OracleConnector)

    # Use the real validate_query method
    real_connector = OracleConnector.__new__(OracleConnector)
    connector.validate_query = real_connector.validate_query

    # Mock execute_query to return sample customer data
    async def mock_execute(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        # Validate first (uses real validation)
        connector.validate_query(sql)

        # Return mock data based on query
        if "CUSTOMERS" in sql.upper():
            return [
                {"CUSTOMER_ID": 1, "NAME": "Acme Corp", "TOTAL_PURCHASES": 150000},
                {"CUSTOMER_ID": 2, "NAME": "GlobalTech", "TOTAL_PURCHASES": 120000},
                {"CUSTOMER_ID": 3, "NAME": "Saudi Industries", "TOTAL_PURCHASES": 95000},
                {"CUSTOMER_ID": 4, "NAME": "Riyadh Trading", "TOTAL_PURCHASES": 87000},
                {"CUSTOMER_ID": 5, "NAME": "Desert Solutions", "TOTAL_PURCHASES": 72000},
            ]
        elif "EMPLOYEES" in sql.upper():
            return [
                {"EMPLOYEE_NAME": "Ahmed", "SALARY": 25000},
                {"EMPLOYEE_NAME": "Sara", "SALARY": 22000},
            ]
        else:
            return [{"RESULT": "Query executed successfully"}]

    connector.execute_query = mock_execute
    return connector


def create_mock_indexer() -> OracleSchemaIndexer:
    """Create a mock OracleSchemaIndexer with sample table metadata."""
    indexer = MagicMock(spec=OracleSchemaIndexer)

    def mock_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()

        if "customer" in query_lower:
            return [
                {
                    "table_name": "CUSTOMERS",
                    "owner": "ERP",
                    "comments": "Master customer records with purchase history",
                    "score": 0.92,
                },
                {
                    "table_name": "CUSTOMER_ORDERS",
                    "owner": "ERP",
                    "comments": "Customer order transactions",
                    "score": 0.78,
                },
            ]
        elif "employee" in query_lower or "salary" in query_lower:
            return [
                {
                    "table_name": "EMPLOYEES",
                    "owner": "HR",
                    "comments": "Employee master data including compensation",
                    "score": 0.95,
                },
            ]
        elif "order" in query_lower:
            return [
                {
                    "table_name": "ORDERS",
                    "owner": "ERP",
                    "comments": "Sales order header records",
                    "score": 0.88,
                },
            ]
        else:
            return []

    indexer.search_tables = mock_search
    return indexer


def print_response(response: AgentResponse) -> None:
    """Pretty print the agent response."""
    print("\n" + "=" * 60)
    print(f"Question: {response.question}")
    print("=" * 60)

    print("\n📊 Relevant Tables Found:")
    for table in response.relevant_tables:
        print(f"  - {table['owner']}.{table['table_name']} (score: {table['score']:.2f})")
        if table.get("comments"):
            print(f"    └─ {table['comments']}")

    print(f"\n🔍 Generated SQL:\n  {response.generated_sql}")

    if response.error:
        print(f"\n❌ Error: {response.error}")
    elif response.results:
        print(f"\n✅ Results ({len(response.results)} rows):")
        for i, row in enumerate(response.results[:5], 1):
            print(f"  {i}. {row}")
        if len(response.results) > 5:
            print(f"  ... and {len(response.results) - 5} more rows")

    print()


async def main() -> None:
    """Run the demo."""
    print("\n🚀 Oracle SQL RAG Agent Demo")
    print("=" * 60)
    print("This demo simulates the full SQL RAG pipeline using mocks.")
    print("In production, this would connect to a real Oracle database.\n")

    # Create mocked components
    connector = create_mock_connector()
    indexer = create_mock_indexer()
    llm = MockLLM()

    # Create the agent
    agent = OracleSQLAgent(connector=connector, indexer=indexer, llm=llm)

    # Test questions
    questions = [
        "Show me top 5 customers by purchases",
        "What are the employee salaries?",
        "List recent orders",
    ]

    for question in questions:
        response = await agent.run(question)
        print_response(response)

    # Demonstrate safety: try a dangerous query
    print("\n⚠️  Testing Safety: Attempting to generate a DELETE query...")
    print("-" * 60)

    # Create a malicious mock LLM that tries to generate DELETE
    @dataclass
    class MaliciousLLM:
        async def generate(self, prompt: str) -> str:
            return "DELETE FROM CUSTOMERS WHERE 1=1"

    malicious_agent = OracleSQLAgent(
        connector=connector, indexer=indexer, llm=MaliciousLLM()
    )
    response = await malicious_agent.run("Delete all customers")
    print_response(response)

    print("✅ Demo complete! The agent safely blocked the dangerous query.")


if __name__ == "__main__":
    asyncio.run(main())
