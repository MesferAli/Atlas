# Product Requirements Document (PRD)

# Atlas — Saudi AI Middleware v2.1

**Document Version:** 2.1.0
**Date:** January 30, 2026
**Owner:** XCircle Enterprise Solutions
**Status:** APPROVED FOR PRODUCTION

---

## Executive Summary

### Product Overview

Atlas (Saudi AI Middleware v2.1) is an enterprise-grade AI orchestration platform hosted on **Alibaba Cloud (Riyadh Region)**. It provides intelligent routing between multiple AI providers (Claude, GPT-4o, ALLaM) with built-in Saudi context understanding, PDPL (Personal Data Protection Law) compliance enforcement, and legacy Oracle/ERP system integration through a natural language "Chat with Data" interface.

### Business Objectives

| # | Objective | Target |
|---|-----------|--------|
| 1 | Reduce AI costs through intelligent multi-provider routing | 30–60% cost reduction |
| 2 | Ensure PDPL compliance with automatic PII detection and local processing | 100% compliance |
| 3 | Bridge legacy systems by enabling "Chat with Data" for Oracle/ERP databases | < 5s query response |
| 4 | Enable enterprise adoption with security, audit trails, and compliance | 5 pilot customers in Q1 |

### Key Differentiators

- **Bilingual AI**: Full Arabic/English support across all interfaces and AI prompts
- **PDPL-First**: Built from the ground up for Saudi data protection compliance
- **Zero-Install Oracle**: Thin Mode connector requires no Oracle Client installation
- **Defense-in-Depth Security**: Six layers of security from input validation to audit logging

---

## 1. Product Vision & Strategy

### 1.1 Vision Statement

> "To become the trusted AI infrastructure layer for Saudi enterprises, enabling secure, compliant, and cost-effective AI adoption at scale."

### 1.2 Target Users

| Role | Description | System Role |
|------|-------------|-------------|
| Enterprise Admin | IT administrators managing platform configuration, users, and security policies | ADMIN |
| Data Analyst | Business analysts querying Oracle/ERP data using natural language | ANALYST |
| Executive Viewer | Management viewing dashboards and reports (read-only) | VIEWER |
| Service Account | System-to-system integrations and automated workflows | SERVICE |

### 1.3 Strategic Goals

#### Q1 2026 (Current — MVP)
- ✅ Launch MVP on Alibaba Cloud SA
- ✅ Onboard 5 enterprise pilot customers
- ✅ Deploy Oracle Connector Lite (Read-Only RAG) for pilot success
- ✅ Achieve PDPL compliance certification

#### Q2 2026 (Growth)
- Expand to 20+ enterprise customers
- Add write-capable Oracle operations (with approval workflows)
- Multi-tenant isolation
- Advanced analytics dashboard

#### Q3–Q4 2026 (Scale)
- SAP and Microsoft Dynamics connectors
- Custom fine-tuned models per customer
- Marketplace for enterprise AI plugins

---

## 2. User Stories & Personas

### 2.1 Data Analyst (Primary Persona)

**As a** data analyst,
**I want to** ask questions about our Oracle ERP data in plain Arabic or English,
**So that** I can get answers without writing SQL or waiting for IT support.

**Acceptance Criteria:**
- User types a natural language question (e.g., "كم عدد الموظفين في قسم المبيعات؟")
- System identifies relevant Oracle tables via semantic search
- System generates read-only SQL and executes it
- Results are displayed in a formatted table
- Full audit trail is logged

### 2.2 Enterprise Admin

**As an** IT administrator,
**I want to** manage user access, view audit logs, and monitor system health,
**So that** I can ensure the platform is secure and compliant.

**Acceptance Criteria:**
- Admin can create/update/delete users with RBAC roles
- Admin can view and filter audit logs by date, event type, and user
- Admin can view aggregate security statistics
- Admin can configure notification and security settings

### 2.3 Executive Viewer

**As a** manager,
**I want to** view the dashboard with key metrics and system status,
**So that** I can understand platform utilization and compliance posture.

**Acceptance Criteria:**
- Dashboard shows Oracle connection status, PDPL compliance status, AI provider status
- Dashboard shows total query count and recent activity
- Read-only access — no configuration changes allowed

---

## 3. Product Features & Requirements

### 3.1 Feature 1: Natural Language to SQL (Oracle Connector Lite)

**Priority:** P0 — Critical
**Status:** ✅ Implemented

**Description:** A secure, read-only agent that answers natural language queries against Oracle Database schemas without modifying data. Users can "Chat with their ERP" using Arabic or English.

**Technical Implementation:**

| Component | Technology | Details |
|-----------|------------|---------|
| Database Driver | `python-oracledb` 2.0 | Thin Mode — no Oracle Client required |
| Connection | Atlas Secure Agent | Encrypted tunnel to on-premises Oracle DB |
| Connection Pool | Async pool | min=1, max=5 connections |
| Vector Search | Qdrant + `all-MiniLM-L6-v2` | 384-dimensional embeddings for table matching |
| LLM (Production) | Fine-tuned Qwen via Unsloth | 4-bit quantized, max 256 tokens, temp=0.1 |
| LLM (Testing) | MockLLM | Pattern-based SQL generation |

**RAG Pipeline:**

```
User Question → Semantic Search (Qdrant) → Find Relevant Tables
    → Build Bilingual Prompt with Schema Context
    → LLM Generates SQL
    → validate_query() enforces READ-ONLY
    → Execute via Thin Mode Connector
    → Return Formatted Results + Audit Trail
```

**Blocked SQL Operations:**
`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `MERGE`, `GRANT`, `REVOKE`, `EXECUTE`, `CALL`

**API Endpoint:** `POST /v1/chat`

**Request:**
```json
{
  "question": "كم عدد الموظفين النشطين؟",
  "max_tables": 5
}
```

**Response:**
```json
{
  "question": "كم عدد الموظفين النشطين؟",
  "relevant_tables": [
    {"table_name": "PER_ALL_PEOPLE_F", "score": 0.87}
  ],
  "generated_sql": "SELECT COUNT(*) FROM PER_ALL_PEOPLE_F WHERE EFFECTIVE_END_DATE IS NULL",
  "results": [{"COUNT(*)": 1250}],
  "execution_time_ms": 340
}
```

### 3.2 Feature 2: Authentication & Authorization

**Priority:** P0 — Critical
**Status:** ✅ Implemented

**Description:** JWT-based authentication with role-based access control (RBAC) supporting four user roles.

| Requirement | Specification |
|-------------|---------------|
| Token Algorithm | HS256 |
| Token Expiration | 24 hours |
| Password Hashing | bcrypt (12 rounds) |
| Password Policy | 8+ chars, uppercase, lowercase, digit |
| RBAC Roles | ADMIN, ANALYST, VIEWER, SERVICE |
| Rate Limiting (Auth) | 10 requests/minute |
| Rate Limiting (General) | 60 requests/minute |

**API Endpoints:**

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/register` | User registration | No |
| POST | `/api/auth/logout` | Session termination | Yes |
| POST | `/api/auth/refresh` | Token refresh | Yes |
| GET | `/api/auth/user` | Current user profile | Yes |

### 3.3 Feature 3: Audit Logging System

**Priority:** P0 — Critical
**Status:** ✅ Implemented

**Description:** Append-only audit logging with daily file rotation for compliance and forensics.

**Event Categories:**

| Category | Events |
|----------|--------|
| Authentication | `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`, `TOKEN_REFRESH`, `PASSWORD_CHANGE`, `MFA_ENABLED`, `MFA_DISABLED` |
| Data Access | `QUERY_EXECUTED`, `QUERY_BLOCKED`, `SCHEMA_ACCESSED`, `EXPORT_REQUESTED` |
| Admin | `USER_CREATED`, `USER_UPDATED`, `USER_DELETED`, `ROLE_CHANGED`, `SETTINGS_CHANGED` |
| Security | `RATE_LIMIT_EXCEEDED`, `INVALID_TOKEN`, `UNAUTHORIZED_ACCESS`, `SUSPICIOUS_ACTIVITY` |

**Storage:** `./logs/audit/audit_YYYY-MM-DD.jsonl` (daily rotation, append-only)

**Sanitization:** Passwords, tokens, and sensitive fields are automatically redacted before logging.

**API Endpoints:**

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/audit/logs` | Query logs with filters (date, type, user) | ADMIN, ANALYST |
| GET | `/api/audit/stats` | Aggregate statistics | ADMIN only |
| GET | `/api/audit/events/{id}` | Retrieve specific event | ADMIN, ANALYST |

### 3.4 Feature 4: PDPL Compliance Engine

**Priority:** P0 — Critical
**Status:** ✅ Implemented

**Description:** Automatic enforcement of Saudi Personal Data Protection Law across all data operations.

**Capabilities:**
- Automatic PII detection in query results
- Data classification enforcement (PUBLIC → TOP_SECRET)
- Row-level security via access predicates per table
- Local data processing — no data leaves Saudi jurisdiction
- Compliance reporting via `/v1/security` endpoint

**Data Classification Levels:**

| Level | Description | Example Tables |
|-------|-------------|----------------|
| PUBLIC | Open data | General lookup tables |
| INTERNAL | Internal use only | Department structures |
| RESTRICTED | Need-to-know basis | Purchase orders, AP invoices |
| SECRET | Highly sensitive | Salary data, payroll relations |
| TOP_SECRET | Maximum protection | Reserved for future use |

### 3.5 Feature 5: Security Middleware

**Priority:** P0 — Critical
**Status:** ✅ Implemented

**Description:** Multi-layer security middleware applied to all API requests.

**Security Headers:**

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | Content security |
| `Permissions-Policy` | geolocation, microphone, camera disabled | Feature policy |
| `Cache-Control` | `no-store` | Prevent caching of API responses |

**Webhook Verification:**
- HMAC-SHA256 signature verification
- Timestamp validation (300-second tolerance)
- Constant-time comparison (timing attack prevention)
- Supported providers: Stripe, LemonSqueezy

### 3.6 Feature 6: Web Dashboard (Frontend SPA)

**Priority:** P1 — High
**Status:** ✅ Implemented

**Description:** React-based single-page application providing the user interface for all platform features.

**Technology Stack:**

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.3.1 |
| Language | TypeScript | 5.6.0 |
| Build Tool | Vite | 5.4.0 |
| Styling | Tailwind CSS | 3.4.0 |
| UI Components | Radix UI | v1.x |
| Routing | Wouter | 3.3.0 |
| Data Fetching | TanStack React Query | 5.60.0 |
| Icons | Lucide React | 0.453.0 |

**Pages:**

| Page | Description | Key Features |
|------|-------------|--------------|
| Landing | Marketing page | Hero, 4 pillars, 5 use cases, FAQ, testimonials |
| Dashboard | Main workspace | Oracle Chat, status cards, quick links |
| Audit | Log viewer | Advanced filtering, pagination, export, event details |
| Settings | Configuration | Tabs: General, Org, Users, Notifications, Security |
| Login | Authentication | Email/password, Google OAuth, bilingual |
| Register | User signup | Full validation, organization selection, terms |
| Forgot Password | Password reset | Email-based recovery |
| Help | Documentation | Getting started guides, FAQ |

**Key UI Components:**
- **OracleChat**: Natural language query input, relevant tables display, SQL viewer, results table
- **AppSidebar**: Navigation with role-based menu items
- **Theme Provider**: Dark/light mode support
- **Language Toggle**: Arabic/English switching with RTL support
- **Export Button**: CSV/JSON export functionality

### 3.7 Feature 7: Multi-Provider AI Routing

**Priority:** P1 — High
**Status:** ✅ Implemented (core routing)

**Description:** Intelligent routing between AI providers based on cost, capability, and compliance requirements.

**Supported Providers:**

| Provider | Use Case | Notes |
|----------|----------|-------|
| Claude (Anthropic) | Complex reasoning, analysis | Primary provider |
| GPT-4o (OpenAI) | General purpose queries | Cost-optimized fallback |
| ALLaM | Arabic-specific tasks | Saudi Arabic understanding |
| Qwen (Unsloth) | SQL generation | Fine-tuned, 4-bit quantized, on-premises |

**API Endpoints:**
- `GET /v1/model` — Current LLM model information and status
- `GET /v1/security` — Security configuration and compliance status

---

## 4. Technical Architecture

### 4.1 System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Alibaba Cloud (Riyadh)                 │
│                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │  React SPA   │───▶│  FastAPI     │───▶│  PostgreSQL  │  │
│  │  (Vite)      │    │  Backend     │    │  (Primary)   │  │
│  └─────────────┘    │             │    └──────────────┘  │
│                      │  ┌────────┐ │    ┌──────────────┐  │
│                      │  │ Auth   │ │───▶│  Redis       │  │
│                      │  │ Audit  │ │    │  (Cache)     │  │
│                      │  │ RBAC   │ │    └──────────────┘  │
│                      │  └────────┘ │    ┌──────────────┐  │
│                      │             │───▶│  Qdrant      │  │
│                      └──────┬──────┘    │  (Vectors)   │  │
│                             │           └──────────────┘  │
│                             │                             │
│                    ┌────────▼────────┐                    │
│                    │ Atlas Secure    │                    │
│                    │ Agent (Tunnel)  │                    │
│                    └────────┬────────┘                    │
└─────────────────────────────┼────────────────────────────┘
                              │ Encrypted
                    ┌─────────▼─────────┐
                    │  On-Premises       │
                    │  Oracle Database   │
                    │  (Fusion ERP)      │
                    └───────────────────┘
```

### 4.2 Infrastructure Stack

| Component | Service | Purpose |
|-----------|---------|---------|
| Compute | ECS (Elastic Compute Service) | Application hosting |
| Orchestration | ACK (Alibaba Container Service for Kubernetes) | Container orchestration |
| Registry | ACR (Enterprise Edition) | Docker image registry |
| Region | Saudi Arabia — Riyadh | Data sovereignty compliance |

### 4.3 Backend Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Web Framework | FastAPI | 0.109.0 |
| ASGI Server | Uvicorn | 0.27.0 |
| Oracle Driver | python-oracledb | 2.0.0 (Thin Mode) |
| Vector DB Client | qdrant-client | 1.7.0 |
| Embeddings | sentence-transformers | 2.2.0 |
| JWT | PyJWT | 2.8.0 |
| Password Hashing | bcrypt | 4.0.0 |
| Validation | Pydantic | 2.x |
| Python | CPython | 3.11+ |

### 4.4 Security Architecture (Defense-in-Depth)

```
Layer 1: Input Validation      → Pydantic v2 models, field sanitization
Layer 2: Authentication        → JWT (HS256, 24h expiry)
Layer 3: Authorization         → RBAC (ADMIN, ANALYST, VIEWER, SERVICE)
Layer 4: Rate Limiting         → 60 req/min general, 10 req/min auth
Layer 5: SQL Validation        → Read-only enforcement (12 blocked keywords)
Layer 6: Audit Logging         → Append-only JSONL, daily rotation
```

### 4.5 Data Classification Schema

The platform enforces data classification on 25+ Oracle Fusion objects defined in `data/oracle_fusion_schema.json`. Each object specifies:

- **classification**: Security level (PUBLIC → TOP_SECRET)
- **min_required_role**: Minimum RBAC role for access
- **access_predicate**: Row-level security SQL condition
- **compliance_standard**: `NDMO_DATA_CLASS_POLICY_V1`

**Key Tables:**

| Table | Classification | Min Role | Description |
|-------|---------------|----------|-------------|
| `PER_ALL_PEOPLE_F` | INTERNAL | ANALYST | Master employee records |
| `PER_ALL_ASSIGNMENTS_M` | RESTRICTED | ANALYST | Employment assignments |
| `CMP_ASG_SALARY` | SECRET | ADMIN | Salary data |
| `PAY_PAYROLL_RELATIONS` | SECRET | ADMIN | Payroll links |
| `PO_HEADERS_ALL` | RESTRICTED | ANALYST | Purchase orders |
| `AP_INVOICES_ALL` | RESTRICTED | ANALYST | AP invoices |

---

## 5. API Specification

### 5.1 Complete Endpoint Map

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/health` | Health check | No | 60/min |
| GET | `/v1/security` | Security config status | No | 60/min |
| GET | `/v1/model` | LLM model info | No | 60/min |
| POST | `/v1/chat` | NL-to-SQL query | Yes | 60/min |
| POST | `/api/auth/login` | User login | No | 10/min |
| POST | `/api/auth/register` | User registration | No | 10/min |
| POST | `/api/auth/logout` | Logout | Yes | 10/min |
| POST | `/api/auth/refresh` | Refresh token | Yes | 10/min |
| GET | `/api/auth/user` | Current user | Yes | 60/min |
| GET | `/api/audit/logs` | Query audit logs | Yes (ADMIN/ANALYST) | 60/min |
| GET | `/api/audit/stats` | Audit statistics | Yes (ADMIN) | 60/min |
| GET | `/api/audit/events/{id}` | Event details | Yes (ADMIN/ANALYST) | 60/min |

### 5.2 Pagination

All list endpoints support pagination:
- `page`: 1–10,000
- `per_page`: 1–100 (default varies by endpoint)

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target |
|--------|--------|
| NL-to-SQL query response | < 5 seconds |
| Authentication response | < 500ms |
| Dashboard load time | < 2 seconds |
| Concurrent users | 100+ |
| Oracle connection pool | 1–5 connections |

### 6.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Data encryption in transit | TLS 1.2+ |
| Password storage | bcrypt (12 rounds) |
| Token security | JWT HS256, 24h expiry |
| SQL injection prevention | Read-only validation + parameterized queries |
| XSS prevention | CSP headers + input sanitization |
| Clickjacking prevention | X-Frame-Options: DENY |
| Audit trail | Append-only, tamper-evident JSONL |

### 6.3 Compliance

| Standard | Status |
|----------|--------|
| PDPL (Saudi Data Protection) | ✅ Compliant |
| NDMO Data Classification Policy v1 | ✅ Enforced |
| Data Residency (Saudi Arabia) | ✅ Alibaba Cloud Riyadh |
| Audit Requirements | ✅ Append-only logging |

### 6.4 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.5% |
| Recovery Time Objective (RTO) | < 1 hour |
| Recovery Point Objective (RPO) | < 5 minutes |
| Deployment | Zero-downtime via ACK rolling updates |

### 6.5 Internationalization

| Requirement | Implementation |
|-------------|----------------|
| Arabic language support | Full UI and AI prompts |
| English language support | Full UI and AI prompts |
| RTL layout | Supported in frontend |
| Bilingual NL-to-SQL | Arabic and English queries accepted |

---

## 7. Environment Configuration

### 7.1 Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ATLAS_JWT_SECRET` / `SECRET_KEY` | JWT signing key | — (required) |
| `ATLAS_JWT_EXPIRATION_HOURS` | Token TTL | 24 |
| `ATLAS_USE_UNSLOTH` | Enable Qwen LLM | false |
| `ATLAS_MODEL_PATH` | Fine-tuned model path | — |
| `ATLAS_QDRANT_PATH` | Qdrant storage | `./qdrant_data` |
| `ATLAS_AUDIT_LOG_DIR` | Audit log dir | `./logs/audit/` |
| `ATLAS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |
| `ORACLE_DSN` | Oracle connection string | — (required) |
| `ORACLE_USER` | Oracle username | — (required) |
| `ORACLE_PASSWORD` | Oracle password | — (required) |
| `QDRANT_URL` | Qdrant endpoint | — |

---

## 8. Testing Strategy

### 8.1 Current Coverage

| Area | Framework | Status |
|------|-----------|--------|
| Oracle Connector (query validation) | pytest + pytest-asyncio | ✅ 11+ test cases |
| SQL injection prevention | pytest | ✅ Covered |
| Case-insensitive keyword detection | pytest | ✅ Covered |
| Schema metadata retrieval | pytest | ✅ Covered |

### 8.2 Test Commands

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_oracle_connector.py

# Specific test
pytest tests/unit/test_oracle_connector.py::TestValidateQuery::test_blocks_insert
```

### 8.3 Known Limitations

- SQL keywords inside string literals are also blocked (conservative security approach)
- MockLLM used in test environments (pattern-based, not AI-generated SQL)

---

## 9. Development Roadmap

### 9.1 Q1 2026 — MVP (CURRENT)

- [x] Oracle Connector Lite (Read-Only, Thin Mode)
- [x] JWT Authentication with RBAC
- [x] Append-only Audit Logging
- [x] PDPL Compliance Engine
- [x] Security Middleware (rate limiting, headers)
- [x] RAG Pipeline (Qdrant + sentence-transformers)
- [x] React Dashboard with OracleChat
- [x] Bilingual Support (Arabic/English)
- [x] Alibaba Cloud SA deployment (ACK + ACR)
- [ ] Oracle Connector Lite deployment for 5 pilot customers

### 9.2 Q2 2026 — Growth

- [ ] Write-capable Oracle operations with approval workflows
- [ ] Multi-tenant isolation
- [ ] Advanced analytics dashboard
- [ ] SAP connector (read-only)
- [ ] Expand to 20+ customers
- [ ] MFA (multi-factor authentication)

### 9.3 Q3–Q4 2026 — Scale

- [ ] SAP and Microsoft Dynamics connectors
- [ ] Custom fine-tuned models per customer
- [ ] AI plugin marketplace
- [ ] Real-time streaming query results
- [ ] Mobile application

---

## 10. Demo & Testing Credentials

| Field | Value |
|-------|-------|
| Email | `demo@atlas.sa` |
| Password | `Demo@123` |
| Role | ANALYST |
| Server | `localhost:8080` |

---

## Appendix A: Code Structure

```
src/atlas/
├── api/
│   ├── main.py                    # FastAPI app, /health, /v1/chat, /v1/security
│   ├── routes/
│   │   ├── auth.py                # /api/auth/* endpoints
│   │   └── audit.py               # /api/audit/* endpoints
│   └── security/
│       ├── auth.py                # JWT + bcrypt authentication
│       ├── models.py              # Pydantic models, RBAC roles
│       ├── audit.py               # Append-only audit logging
│       ├── middleware.py          # Rate limiting, security headers
│       └── webhooks.py            # Webhook HMAC verification
├── connectors/oracle/
│   ├── connector.py               # OracleConnector: validate_query() + execution
│   └── indexer.py                 # OracleSchemaIndexer: Qdrant semantic search
├── agent/
│   ├── sql_agent.py               # OracleSQLAgent: NL-to-SQL RAG pipeline
│   └── unsloth_llm.py            # Qwen model via Unsloth (4-bit)
└── frontend/
    └── src/
        ├── App.tsx                # Main app with routing
        ├── pages/                 # 9 pages (dashboard, audit, settings, etc.)
        ├── components/            # Radix UI + domain components
        ├── hooks/                 # use-auth.ts, use-toast.ts
        └── lib/                   # queryClient.ts, utils.ts, i18n.ts
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| ACK | Alibaba Container Service for Kubernetes |
| ACR | Alibaba Cloud Container Registry |
| ALLaM | Arabic large language model |
| NDMO | National Data Management Office (Saudi Arabia) |
| NL-to-SQL | Natural Language to SQL conversion |
| PDPL | Personal Data Protection Law (Saudi Arabia) |
| RAG | Retrieval-Augmented Generation |
| RBAC | Role-Based Access Control |
| Thin Mode | python-oracledb connection mode requiring no Oracle Client |
| Unsloth | Fast LLM inference library for fine-tuned models |
