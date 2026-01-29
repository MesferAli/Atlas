# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Atlas is an enterprise AI orchestration platform (Saudi AI Middleware v2.1) that provides:
- Multi-provider AI routing (Claude, GPT-4o, ALLaM) with cost optimization
- Oracle Connector Lite: Read-only natural language queries against Oracle databases via `python-oracledb` thin mode
- PDPL (Personal Data Protection Law) compliance enforcement with automatic PII detection
- Atlas Secure Agent encrypted tunneling for legacy database connections
- Bilingual support (Arabic/English) throughout the platform

## Architecture

**Cloud**: Alibaba Cloud (Riyadh) using ACK (Kubernetes) and ACR (Container Registry)

**Data Layer**: PostgreSQL (primary), Redis (caching), Qdrant (vector search)

**Oracle Integration**: Uses `python-oracledb` in Thin Mode (no Oracle Client installation required) through the Atlas Secure Agent tunnel. All Oracle queries must be strictly read-only — no DDL/DML operations allowed.

**AI Providers**: Requests are intelligently routed between Claude, GPT-4o, and ALLaM based on cost and capability requirements. Production uses a fine-tuned Qwen model via Unsloth (4-bit quantized).

**Frontend**: React 18 + TypeScript with Vite, Tailwind CSS, and Radix UI components. Uses Wouter for routing and React Query for data fetching.

**Backend**: FastAPI with Pydantic v2 validation, JWT authentication (bcrypt + HS256), and layered security middleware.

## Code Structure

```
src/atlas/
├── api/                          # FastAPI backend
│   ├── main.py                   # App entry point, /health, /v1/chat, /v1/security
│   ├── routes/
│   │   ├── auth.py               # /api/auth/* (login, register, logout, refresh)
│   │   └── audit.py              # /api/audit/* (logs, stats, events)
│   └── security/
│       ├── auth.py               # JWT + bcrypt authentication
│       ├── models.py             # Pydantic request/response models, RBAC roles
│       ├── audit.py              # Append-only audit logging (JSONL, daily rotation)
│       ├── middleware.py         # Rate limiting, security headers, request logging
│       └── webhooks.py           # Webhook handling
├── connectors/oracle/
│   ├── connector.py              # OracleConnector: validate_query() + read-only execution
│   └── indexer.py                # OracleSchemaIndexer: semantic search via Qdrant
├── agent/
│   ├── sql_agent.py              # OracleSQLAgent: NL-to-SQL with RAG pipeline
│   └── unsloth_llm.py           # Qwen model integration via Unsloth
└── frontend/                     # React TypeScript SPA
    ├── src/
    │   ├── App.tsx               # Main app with routing
    │   ├── pages/                # dashboard, audit, settings, login, register, etc.
    │   ├── components/
    │   │   ├── atlas/            # Domain-specific components
    │   │   └── ui/               # Radix UI primitives
    │   ├── hooks/                # use-auth.ts, use-toast.ts
    │   └── lib/                  # queryClient.ts, utils.ts, i18n.ts
    ├── vite.config.ts
    └── tailwind.config.ts

data/
└── oracle_fusion_schema.json     # 25+ Oracle Fusion objects with security metadata

scripts/
├── atlas_chat.py                 # Interactive CLI chat with role-based access
├── demo_agent.py                 # Demo agent script
├── apply_data_classification.py  # Data classification utility
└── inject_moat.py                # Data Moat injection utility

tests/
└── unit/
    └── test_oracle_connector.py  # Query validation and security tests

docs/
└── PRD.md                        # Product Requirements Document
```

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

# Start the API server
uvicorn src.atlas.api.main:app --host 0.0.0.0 --port 8080

# Frontend development
cd src/atlas/frontend && npm install && npm run dev

# Docker build
docker build -t atlas-api .
```

## Core Principles

These principles guide all development on this project:

1. **Security-first**: Every change must preserve read-only Oracle enforcement, PDPL compliance, and audit logging. Never weaken security controls.
2. **Plan before implementing**: Break complex tasks into steps. Understand existing code before modifying it.
3. **Test-driven**: Write or update tests for any new functionality. Run `pytest` to verify before committing.
4. **Validate before committing**: Run `ruff check src/ tests/` and `pytest` before every commit. Fix all failures.
5. **Small, focused changes**: Prefer many small commits over large monolithic ones. Each commit should do one thing.

## Security Rules (Critical)

These rules are **non-negotiable** and must never be bypassed:

- **All Oracle queries must be read-only.** The `validate_query()` method in `connector.py` blocks INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, GRANT, REVOKE, EXECUTE, and CALL.
- **Never bypass query validation.** All SQL must pass through `validate_query()` before execution.
- **Never hardcode secrets.** Use environment variables for credentials, API keys, and signing keys.
- **PDPL compliance is mandatory.** PII detection and data classification must be maintained.
- **Audit logging is append-only.** All query executions and security events are logged to `./logs/audit/` in JSONL format. Never delete or modify audit logs.
- **Passwords and tokens redacted in logs.** The audit system sanitizes sensitive fields automatically.
- **Validate all user input.** Use Pydantic models for request validation. Sanitize for null bytes and injection attacks.
- **Never commit `.env` files, credentials, or secrets** to the repository.

## Authentication & Authorization

- JWT tokens with 24-hour expiration (HS256)
- RBAC roles: ADMIN, ANALYST, VIEWER, SERVICE
- Password requirements: 8+ chars, uppercase, lowercase, digit
- Demo credentials: `demo@atlas.sa` / `Demo@123` (ANALYST role)
- Rate limiting: 60 req/min general, 10 req/min for auth endpoints

## Data Classification

Oracle Fusion tables have classification levels defined in `data/oracle_fusion_schema.json`:
- PUBLIC, INTERNAL, RESTRICTED, SECRET, TOP_SECRET
- Each table specifies required RBAC roles and access predicates
- Salary and payroll tables are classified as SECRET
- Always check classification before adding new table access

## Code Style

### Python (Backend)
- Python 3.11+, line length 100 (configured in pyproject.toml via ruff)
- Async/await patterns for Oracle connections and API endpoints
- Pydantic v2 models for all request/response validation
- Type hints on all function signatures
- Organize by feature, not by file type
- Use try/except with specific exception types — never bare `except:`

### TypeScript (Frontend)
- TypeScript strict mode
- Tailwind CSS utility classes for styling
- Radix UI primitives for accessible components
- React Query for server state management
- Wouter for routing (not react-router)

## Git Workflow

- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit directly to `main` — use feature branches
- Run linting and tests before committing
- Write descriptive commit messages explaining *why*, not just *what*

## NL-to-SQL Pipeline

1. User question enters via `/v1/chat`
2. Semantic search finds relevant tables (sentence-transformers → Qdrant)
3. LLM generates SQL with schema context (bilingual Arabic/English prompts)
4. Query validated as read-only via `validate_query()`
5. Executed against Oracle via Thin Mode connector
6. Results returned with full audit trail

## Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/v1/chat` | POST | NL-to-SQL query processing |
| `/v1/security` | GET | Security configuration status |
| `/v1/model` | GET | Active LLM model info |
| `/api/auth/login` | POST | User authentication |
| `/api/auth/register` | POST | New user registration |
| `/api/auth/logout` | POST | Token invalidation |
| `/api/auth/refresh` | POST | Token refresh |
| `/api/audit/logs` | GET | Query audit logs (RBAC enforced) |
| `/api/audit/stats` | GET | Audit statistics (admin only) |

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `ATLAS_USE_UNSLOTH` | Enable Unsloth/Qwen LLM | disabled (uses mock) |
| `ATLAS_AUDIT_LOG_DIR` | Audit log directory | `./logs/audit/` |
| `SECRET_KEY` | JWT signing key | — |
| `ORACLE_DSN` | Oracle connection string | — |
| `ORACLE_USER` | Oracle username | — |
| `ORACLE_PASSWORD` | Oracle password | — |
| `QDRANT_URL` | Qdrant vector DB endpoint | — |

## Debugging Tips

- **API not starting**: Check that port 8080 is free. Verify `SECRET_KEY` is set.
- **Oracle connection fails**: Atlas uses Thin Mode — no Oracle Client needed. Check `ORACLE_DSN` format.
- **Tests failing on imports**: Ensure `pip install -e ".[dev]"` was run and `pythonpath = ["src"]` is set in pyproject.toml.
- **Frontend build errors**: Run `npm install` in `src/atlas/frontend/` first. Check Node.js 18+ is installed.
- **Audit logs missing**: Check `ATLAS_AUDIT_LOG_DIR` points to a writable directory.
