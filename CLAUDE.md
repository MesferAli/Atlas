# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Atlas is an enterprise AI orchestration platform (Saudi AI Middleware v2.1) that provides:
- Multi-provider AI routing (Claude, GPT-4o, ALLaM) with cost optimization
- Oracle Connector Lite: Read-only natural language queries against Oracle databases via `python-oracledb` thin mode
- PDPL compliance enforcement with automatic PII detection
- Atlas Secure Agent encrypted tunneling for legacy database connections

## Architecture

**Cloud**: Alibaba Cloud (Riyadh) using ACK (Kubernetes) and ACR (Container Registry)

**Data Layer**: PostgreSQL (primary), Redis (caching), Qdrant (vector search)

**Oracle Integration**: Uses `python-oracledb` in Thin Mode (no Oracle Client installation required) through the Atlas Secure Agent tunnel. All Oracle queries must be strictly read-only - no DDL/DML operations allowed.

**AI Providers**: Requests are intelligently routed between Claude, GPT-4o, and ALLaM based on cost and capability requirements.

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_oracle_connector.py

# Run a specific test
pytest tests/unit/test_oracle_connector.py::TestValidateQuery::test_blocks_insert

# Lint code
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

## Code Structure

```
src/atlas/
├── connectors/oracle/    # Oracle Connector Lite (read-only DB access)
│   ├── connector.py      # OracleConnector class with validate_query() security
│   └── indexer.py        # OracleSchemaIndexer for RAG-based schema search
├── agent/
│   └── sql_agent.py      # OracleSQLAgent for NL-to-SQL with RAG pipeline
```
