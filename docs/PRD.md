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
- Advanced analytics dashboard

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

### 3.7 Feature 7: AI Provider (Claude Primary)

**Priority:** P1 — High
**Status:** ✅ Implemented

**Description:** Claude as the primary AI provider for NL-to-SQL generation, with MockLLM for testing environments.

**Provider Stack (MVP):**

| Provider | Use Case | Notes |
|----------|----------|-------|
| Claude (Anthropic) | NL-to-SQL generation, reasoning | Primary production provider |
| MockLLM | Testing and development | Pattern-based SQL generation |

> **Q2 Planned:** GPT-4o as cost-optimized fallback.

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
- [ ] GPT-4o as cost-optimized fallback provider
- [ ] SAP connector (read-only)
- [ ] Expand to 20+ customers
- [ ] MFA (multi-factor authentication)
- [ ] SAML/SSO for enterprise customers
- [ ] Qdrant cluster mode for high availability

### 9.3 Q3–Q4 2026 — Scale

- [ ] SAP and Microsoft Dynamics connectors
- [ ] Advanced analytics dashboard

---

## 19. Demo & Testing Credentials

| Field | Value |
|-------|-------|
| Email | `demo@atlas.sa` |
| Password | `Demo@123` |
| Role | ANALYST |
| Server | `localhost:8080` |

---

## 10. Competitive Analysis

### 10.1 Market Landscape

| المنافس | الوصف | نقاط القوة | نقاط الضعف |
|---------|-------|-----------|------------|
| **LangChain + Custom** | إطار عمل مفتوح المصدر يُستخدم لبناء حلول NL-to-SQL داخلية | مرن، مجتمع كبير، مفتوح المصدر | يتطلب بناء داخلي كامل، لا دعم PDPL، لا دعم عربي أصلي |
| **Dataherald** | منصة NL-to-SQL سحابية | واجهة سهلة، دعم متعدد لقواعد البيانات | لا يدعم Oracle Fusion، لا امتثال PDPL، لا استضافة سعودية |
| **AI2SQL** | أداة SaaS لتحويل الأسئلة إلى SQL | سهولة الاستخدام، سعر منخفض | لا يدعم المؤسسات، لا RBAC، لا تدقيق، لا دعم عربي |
| **Amazon Bedrock + QuickSight** | حلول AWS للذكاء الاصطناعي والتحليلات | نظام AWS المتكامل، قابلية التوسع | لا منطقة سعودية (أقرب: البحرين)، تكلفة عالية، قفل مزود |
| **Microsoft Copilot for Power BI** | مساعد ذكاء اصطناعي مدمج في Power BI | تكامل Microsoft، واجهة مألوفة | يتطلب ترخيص E5، لا دعم Oracle مباشر، لا استضافة محلية |

### 10.2 Competitive Advantages (الميزات التنافسية لـ Atlas)

| الميزة | Atlas | المنافسون |
|--------|-------|-----------|
| استضافة داخل السعودية (Alibaba Cloud Riyadh) | ✅ | ❌ معظمهم خارج المملكة |
| امتثال PDPL مدمج | ✅ تلقائي | ❌ يتطلب تخصيص |
| دعم عربي أصلي (واجهة + ذكاء اصطناعي) | ✅ ثنائي اللغة | ⚠️ محدود أو غير موجود |
| تكامل Oracle Fusion بدون تثبيت عميل | ✅ Thin Mode | ❌ يتطلب Oracle Client |
| تصنيف بيانات NDMO | ✅ 5 مستويات | ❌ غير مدعوم |
| توجيه متعدد لمزودي الذكاء الاصطناعي | ✅ 4 مزودين | ⚠️ مزود واحد عادةً |
| نموذج LLM محلي (Qwen/Unsloth) | ✅ لا خروج بيانات | ❌ يعتمد على السحابة |
| سجل تدقيق ثابت (Append-Only) | ✅ JSONL يومي | ⚠️ متفاوت |

### 10.3 Market Positioning

```
                    High Security & Compliance
                            ▲
                            │
                   Atlas ●  │
                            │
    Simple ◄────────────────┼────────────────► Enterprise
                            │
                            │  ● AI2SQL
                            │
                    Low Security & Compliance
```

Atlas يستهدف الربع العلوي الأيمن: **حلول مؤسسية عالية الأمان والامتثال** — وهو القطاع الأقل تغطية في السوق السعودي.

---

## 11. Success Metrics & KPIs (مؤشرات النجاح)

### 11.1 Business KPIs

| المؤشر | الهدف (Q1 2026) | الهدف (Q2 2026) | طريقة القياس |
|--------|-----------------|-----------------|--------------|
| عدد العملاء التجريبيين | 5 | 20 | CRM |
| معدل تحويل التجربة → اشتراك | — | 60% | CRM |
| تقليل تكلفة الذكاء الاصطناعي للعميل | 30% | 45% | مقارنة فواتير المزودين |
| صافي نقاط الترويج (NPS) | — | > 40 | استبيان ربع سنوي |
| الإيرادات الشهرية المتكررة (MRR) | — | 150,000 ر.س | نظام الفوترة |

### 11.2 Product KPIs

| المؤشر | الهدف | طريقة القياس |
|--------|-------|--------------|
| دقة تحويل NL-to-SQL | > 85% | مقارنة النتائج بالاستعلام المتوقع |
| زمن استجابة الاستعلام (P95) | < 5 ثوانٍ | مراقبة APM |
| معدل نجاح الاستعلامات | > 95% | سجلات التدقيق |
| عدد الاستعلامات اليومية لكل مستخدم | > 10 | سجلات التدقيق |
| معدل اعتماد الميزات | > 70% | تحليلات الاستخدام |

### 11.3 Technical KPIs

| المؤشر | الهدف | طريقة القياس |
|--------|-------|--------------|
| وقت التشغيل (Uptime) | 99.5% | مراقبة البنية التحتية |
| زمن استجابة API (P99) | < 2 ثانية | مراقبة APM |
| معدل الأخطاء (Error Rate) | < 1% | سجلات التطبيق |
| استعلامات محظورة أمنياً | 100% اكتشاف | اختبارات الاختراق |
| تغطية الاختبارات | > 80% | pytest --cov |
| زمن الاسترداد (MTTR) | < 30 دقيقة | سجلات الحوادث |

### 11.4 Compliance KPIs

| المؤشر | الهدف | طريقة القياس |
|--------|-------|--------------|
| امتثال PDPL | 100% | تدقيق خارجي |
| تصنيف البيانات مُطبَّق | 100% من الجداول | فحص تلقائي |
| سجلات التدقيق مكتملة | 100% من العمليات | مراجعة دورية |
| حوادث تسرب بيانات | 0 | تقارير الأمان |
| اجتياز اختبار الاختراق | نعم | تدقيق سنوي |

---

## 12. Risk Analysis (تحليل المخاطر)

### 12.1 Technical Risks (مخاطر تقنية)

| # | المخاطرة | الاحتمال | التأثير | خطة التخفيف |
|---|---------|----------|---------|-------------|
| T1 | فشل اتصال Oracle عبر النفق المشفر | متوسط | عالٍ | Connection pooling مع إعادة محاولة تلقائية، مراقبة صحة النفق كل 30 ثانية، تنبيهات فورية |
| T2 | دقة منخفضة في تحويل NL-to-SQL | متوسط | عالٍ | تحسين مستمر للنموذج، جمع feedback من المستخدمين، توسيع بيانات التدريب، fallback لنموذج احتياطي |
| T3 | تجاوز حدود أداء Qdrant مع نمو البيانات | منخفض | متوسط | مراقبة حجم المجموعات، تقسيم أفقي (sharding)، تنظيف دوري للبيانات القديمة |
| T4 | ثغرات أمنية في التبعيات (Dependencies) | متوسط | عالٍ | فحص دوري بـ `pip-audit`، تحديث فوري للثغرات الحرجة، تثبيت إصدارات محددة |
| T5 | تعطل Alibaba Cloud Riyadh Region | منخفض | حرج | خطة DR مع نسخ احتياطي خارج المنطقة، RTO < 1 ساعة |

### 12.2 Business Risks (مخاطر تجارية)

| # | المخاطرة | الاحتمال | التأثير | خطة التخفيف |
|---|---------|----------|---------|-------------|
| B1 | بطء تبني العملاء المؤسسيين | متوسط | عالٍ | برنامج تجريبي مجاني 90 يوماً، فريق نجاح عملاء مخصص، دراسات حالة |
| B2 | تغيير في تنظيمات PDPL | منخفض | عالٍ | متابعة مستمرة لتحديثات SDAIA، بنية مرنة قابلة للتعديل، مستشار قانوني |
| B3 | منافسة من مزودي السحابة الكبار | متوسط | متوسط | التركيز على التخصص السعودي (PDPL، عربي، Oracle Fusion)، سرعة التنفيذ |
| B4 | ارتفاع تكاليف مزودي الذكاء الاصطناعي | متوسط | متوسط | توجيه ذكي متعدد المزودين، نموذج Qwen محلي كبديل، تفاوض على تسعير مؤسسي |
| B5 | فقدان كوادر تقنية رئيسية | متوسط | عالٍ | توثيق شامل، مشاركة المعرفة، حوافز استبقاء |

### 12.3 Security Risks (مخاطر أمنية)

| # | المخاطرة | الاحتمال | التأثير | خطة التخفيف |
|---|---------|----------|---------|-------------|
| S1 | محاولة SQL Injection عبر NL-to-SQL | عالٍ | حرج | `validate_query()` يحظر 12 عملية، استعلامات معلمة (parameterized)، اختبارات اختراق دورية |
| S2 | تسرب بيانات حساسة (رواتب، بيانات شخصية) | منخفض | حرج | تصنيف بيانات NDMO، RBAC صارم، كشف PII تلقائي، تشفير في النقل والتخزين |
| S3 | اختراق JWT tokens | منخفض | عالٍ | انتهاء 24 ساعة، تدوير مفتاح التوقيع، مراقبة أنماط الاستخدام غير الطبيعية |
| S4 | هجمات DDoS على API | متوسط | متوسط | Rate limiting (60/10 req/min)، WAF على مستوى Alibaba Cloud، تدرج تلقائي |

### 12.4 Risk Matrix (مصفوفة المخاطر)

```
التأثير
  حرج │ T5        S1,S2
  عالٍ │ B5,S3     T1,T2,T4,B1
متوسط │           B3,B4,S4    T3
منخفض │
       └──────────────────────────
         منخفض    متوسط      عالٍ
                 الاحتمال
```

---

## 13. Cost Analysis (تحليل التكاليف)

### 13.1 Infrastructure Costs (تكاليف البنية التحتية الشهرية)

| المكوّن | الخدمة | المواصفات | التكلفة الشهرية (تقديرية) |
|--------|--------|----------|--------------------------|
| Compute | Alibaba ECS | 4 vCPU, 16GB RAM × 2 instances | 3,000 ر.س |
| Kubernetes | ACK Pro | Managed cluster, 3 nodes | 2,500 ر.س |
| Container Registry | ACR EE | Enterprise Edition | 500 ر.س |
| Database | PostgreSQL (ApsaraDB RDS) | 4 vCPU, 16GB, 200GB SSD | 2,000 ر.س |
| Cache | Redis (ApsaraDB) | 4GB | 800 ر.س |
| Vector DB | Qdrant (self-hosted on ECS) | 2 vCPU, 8GB RAM | 1,200 ر.س |
| Storage | OSS (Object Storage) | 500GB backups + logs | 200 ر.س |
| Networking | SLB + Bandwidth | Load balancer + 100Mbps | 1,000 ر.س |
| Security | WAF + SSL | Web Application Firewall | 800 ر.س |
| **الإجمالي** | | | **~12,000 ر.س/شهر** |

### 13.2 AI Provider Costs (تكاليف مزودي الذكاء الاصطناعي)

| المزود | التسعير | الاستخدام المقدر (شهرياً) | التكلفة الشهرية |
|--------|---------|--------------------------|----------------|
| Claude (Anthropic) | ~$15/M input tokens | 2M tokens | 450 ر.س |
| GPT-4o (OpenAI) | ~$5/M input tokens | 3M tokens | 225 ر.س |
| ALLaM | تسعير مؤسسي | 1M tokens | 150 ر.س |
| Qwen (Unsloth — محلي) | تكلفة GPU فقط | غير محدود | 0 ر.س (مدمج في ECS) |
| **الإجمالي** | | | **~825 ر.س/شهر** |

### 13.3 Operational Costs (تكاليف تشغيلية)

| البند | التكلفة الشهرية |
|-------|----------------|
| فريق التطوير والصيانة | حسب الهيكل التنظيمي |
| دعم فني (L1/L2) | حسب الهيكل التنظيمي |
| تدقيق أمني سنوي (مقسّم شهرياً) | 2,500 ر.س |
| تراخيص أدوات المراقبة | 500 ر.س |
| **الإجمالي التشغيلي** | **~3,000 ر.س/شهر** |

### 13.4 Total Cost of Ownership (إجمالي تكلفة التملك)

| البند | الشهري | السنوي |
|-------|--------|--------|
| البنية التحتية | 12,000 ر.س | 144,000 ر.س |
| مزودو الذكاء الاصطناعي | 825 ر.س | 9,900 ر.س |
| تشغيلي | 3,000 ر.س | 36,000 ر.س |
| **الإجمالي** | **~15,825 ر.س** | **~189,900 ر.س** |

> *ملاحظة: التكاليف تقديرية وتتغير حسب حجم الاستخدام وعدد العملاء.*

### 13.5 Pricing Model (نموذج التسعير المقترح)

| الخطة | السعر الشهري | المستخدمون | الاستعلامات/شهر | الدعم |
|-------|-------------|-----------|----------------|-------|
| Starter | 5,000 ر.س | حتى 10 | 5,000 | بريد إلكتروني |
| Professional | 15,000 ر.س | حتى 50 | 25,000 | أولوية + SLA |
| Enterprise | تسعير مخصص | غير محدود | غير محدود | مدير حساب مخصص |

---

## 14. Support & Maintenance Plan (خطة الدعم والصيانة)

### 14.1 Service Level Agreements (اتفاقيات مستوى الخدمة)

| مستوى الخطورة | التعريف | زمن الاستجابة | زمن الحل |
|---------------|---------|--------------|----------|
| P1 — حرج | النظام متوقف بالكامل أو تسرب بيانات | 30 دقيقة | 4 ساعات |
| P2 — عالٍ | ميزة رئيسية معطلة (مثل: NL-to-SQL لا يعمل) | ساعة واحدة | 8 ساعات |
| P3 — متوسط | مشكلة تؤثر على الأداء أو ميزة ثانوية | 4 ساعات | 24 ساعة |
| P4 — منخفض | طلب تحسين أو سؤال عام | يوم عمل | 5 أيام عمل |

### 14.2 Support Channels (قنوات الدعم)

| القناة | التوفر | الخطط المشمولة |
|--------|--------|---------------|
| بوابة الدعم (Ticketing) | 24/7 | جميع الخطط |
| بريد إلكتروني (support@atlas.sa) | ساعات العمل (8ص–6م) | جميع الخطط |
| هاتف مباشر | ساعات العمل | Professional, Enterprise |
| مدير حساب مخصص | ساعات العمل | Enterprise فقط |
| دعم طوارئ (On-Call) | 24/7 | Enterprise فقط |

### 14.3 Maintenance Windows (نوافذ الصيانة)

| النوع | التوقيت | الإشعار المسبق | التأثير |
|-------|--------|---------------|---------|
| صيانة مجدولة | الخميس 11م–2ص (بتوقيت الرياض) | 72 ساعة | قد يتأثر الأداء |
| تحديث أمني طارئ | فوري | أسرع وقت ممكن | توقف مؤقت محتمل |
| تحديثات ميزات | خلال نوافذ الصيانة | أسبوع | Zero-downtime عبر rolling update |

### 14.4 Monitoring & Alerting (المراقبة والتنبيه)

| المكوّن | الأداة | ما يُراقَب |
|--------|-------|-----------|
| صحة التطبيق | Health endpoint (`/health`) | حالة الخدمة كل 30 ثانية |
| الأداء | APM metrics | زمن الاستجابة، معدل الأخطاء، throughput |
| البنية التحتية | Alibaba CloudMonitor | CPU، ذاكرة، قرص، شبكة |
| الأمان | سجلات التدقيق + تنبيهات | محاولات اختراق، تجاوز rate limit |
| قواعد البيانات | Database monitoring | اتصالات، استعلامات بطيئة، مساحة التخزين |

### 14.5 Escalation Matrix (مصفوفة التصعيد)

```
المستوى 1 (L1): فريق الدعم الفني
    ↓ (إذا لم يُحل خلال SLA)
المستوى 2 (L2): مهندسو المنصة
    ↓ (إذا لم يُحل أو P1)
المستوى 3 (L3): فريق التطوير الأساسي
    ↓ (إذا تأثر أكثر من عميل)
الإدارة: مدير المنتج + CTO
```

---

## 15. Migration & Onboarding Plan (خطة الترحيل والتأهيل)

### 15.1 Customer Onboarding Journey (رحلة تأهيل العميل)

```
الأسبوع 1              الأسبوع 2              الأسبوع 3              الأسبوع 4
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────┐
│ الاكتشاف  │─────▶│ الإعداد التقني │─────▶│ التدريب      │─────▶│ الإطلاق   │
│ والتقييم  │      │ والربط       │      │ والاختبار    │      │ والمتابعة │
└──────────┘      └──────────────┘      └──────────────┘      └──────────┘
```

### 15.2 Phase 1: Discovery & Assessment (الاكتشاف والتقييم) — الأسبوع 1

| النشاط | المسؤول | المخرجات |
|--------|---------|---------|
| تحليل بيئة Oracle للعميل | فريق Atlas + IT العميل | قائمة الجداول والمخططات |
| تصنيف البيانات حسب NDMO | فريق Atlas | مستند تصنيف البيانات |
| تحديد المستخدمين والصلاحيات | IT العميل | قائمة المستخدمين وأدوارهم |
| مراجعة متطلبات الشبكة | فريق Atlas + IT العميل | مخطط الاتصال |

### 15.3 Phase 2: Technical Setup (الإعداد التقني) — الأسبوع 2

| النشاط | المسؤول | المخرجات |
|--------|---------|---------|
| تثبيت Atlas Secure Agent | فريق Atlas | نفق مشفر فعّال |
| ربط Oracle Database (Thin Mode) | فريق Atlas | اتصال مؤكد |
| فهرسة مخططات Oracle في Qdrant | فريق Atlas | فهرس دلالي جاهز |
| تهيئة المستخدمين وصلاحيات RBAC | IT العميل | حسابات مُفعّلة |
| تطبيق تصنيف البيانات | فريق Atlas | قواعد الوصول مُطبّقة |

### 15.4 Phase 3: Training & Testing (التدريب والاختبار) — الأسبوع 3

| النشاط | المسؤول | المخرجات |
|--------|---------|---------|
| تدريب المسؤولين (ADMIN) | فريق Atlas | جلسة 2 ساعة |
| تدريب المحللين (ANALYST) | فريق Atlas | جلسة 1 ساعة |
| اختبار قبول المستخدم (UAT) | العميل | تقرير UAT |
| اختبار الأداء والأمان | فريق Atlas | تقرير اختبار |

### 15.5 Phase 4: Go-Live & Hypercare (الإطلاق والمتابعة) — الأسبوع 4

| النشاط | المسؤول | المخرجات |
|--------|---------|---------|
| إطلاق الإنتاج | فريق Atlas | النظام مباشر |
| مراقبة مكثفة (Hypercare) | فريق Atlas | تقارير يومية لمدة أسبوعين |
| جلسات مراجعة أسبوعية | مدير الحساب | تقرير أداء |
| تسليم للدعم العادي | فريق Atlas | انتقال إلى SLA القياسي |

### 15.6 Prerequisites (المتطلبات المسبقة من العميل)

- [ ] Oracle Database متاح عبر الشبكة (منفذ 1521 أو مخصص)
- [ ] حساب Oracle بصلاحيات SELECT فقط على الجداول المطلوبة
- [ ] قائمة المستخدمين المراد تسجيلهم مع أدوارهم
- [ ] موافقة فريق أمن المعلومات على الربط
- [ ] بيئة اختبار (Staging) متاحة للتهيئة الأولية

---

## 16. Disaster Recovery Plan (خطة التعافي من الكوارث)

### 16.1 Recovery Objectives

| المقياس | الهدف | التفاصيل |
|--------|-------|---------|
| RTO (Recovery Time Objective) | < 1 ساعة | الزمن الأقصى لاستعادة الخدمة |
| RPO (Recovery Point Objective) | < 5 دقائق | الحد الأقصى لفقدان البيانات |
| MTTR (Mean Time To Recovery) | < 30 دقيقة | متوسط زمن الاسترداد |

### 16.2 Backup Strategy (استراتيجية النسخ الاحتياطي)

| المكوّن | نوع النسخ | التكرار | الاحتفاظ | الموقع |
|--------|----------|---------|----------|--------|
| PostgreSQL | Full + WAL streaming | يومي + مستمر | 30 يوماً | Alibaba OSS (Riyadh) |
| Redis | RDB snapshots | كل 6 ساعات | 7 أيام | Alibaba OSS |
| Qdrant | Collection snapshots | يومي | 14 يوماً | Alibaba OSS |
| سجلات التدقيق | نسخ ملفات JSONL | يومي | 365 يوماً | Alibaba OSS (نسخة ثانية) |
| تهيئات Kubernetes | etcd snapshots | يومي | 30 يوماً | Alibaba OSS |
| كود المصدر | Git repository | مستمر | غير محدود | GitHub |

### 16.3 Failure Scenarios & Recovery Procedures

#### السيناريو 1: فشل Pod/Container واحد
- **الاكتشاف**: Kubernetes health checks (30 ثانية)
- **الاسترداد**: إعادة تشغيل تلقائية عبر Kubernetes
- **RTO**: < 1 دقيقة
- **التأثير**: لا تأثير (replicas متعددة)

#### السيناريو 2: فشل قاعدة البيانات (PostgreSQL)
- **الاكتشاف**: مراقبة اتصال قاعدة البيانات
- **الاسترداد**: تفعيل النسخة الاحتياطية (ApsaraDB failover تلقائي)
- **RTO**: < 5 دقائق
- **RPO**: < 1 دقيقة (WAL streaming)

#### السيناريو 3: فشل منطقة Alibaba Cloud بالكامل
- **الاكتشاف**: مراقبة خارجية
- **الاسترداد**: تفعيل خطة DR في منطقة بديلة
- **RTO**: < 1 ساعة
- **RPO**: < 5 دقائق

#### السيناريو 4: فقدان اتصال Oracle (Atlas Secure Agent)
- **الاكتشاف**: فحص صحة النفق كل 30 ثانية
- **الاسترداد**: إعادة إنشاء النفق تلقائياً + إخطار العميل
- **RTO**: < 2 دقيقة
- **التأثير**: استعلامات Oracle تفشل مؤقتاً، باقي النظام يعمل

### 16.4 DR Testing (اختبار خطة التعافي)

| الاختبار | التكرار | المسؤول |
|---------|---------|---------|
| استعادة قاعدة بيانات من نسخة احتياطية | ربع سنوي | فريق البنية التحتية |
| محاكاة فشل Pod والتعافي التلقائي | شهري | فريق DevOps |
| اختبار DR كامل (failover إلى منطقة بديلة) | نصف سنوي | جميع الفرق |
| مراجعة وتحديث خطة DR | سنوي | مدير المنتج + CTO |

---

## 17. Stakeholders & Sign-off (أصحاب المصلحة والموافقات)

### 17.1 RACI Matrix

| النشاط | Product Owner | Tech Lead | Security Lead | DevOps | Frontend Lead |
|--------|:---:|:---:|:---:|:---:|:---:|
| تعريف متطلبات المنتج | R/A | C | C | I | C |
| تصميم البنية التقنية | C | R/A | C | C | I |
| تنفيذ الأمان والامتثال | I | C | R/A | C | I |
| نشر البنية التحتية | I | C | C | R/A | I |
| تطوير الواجهة الأمامية | C | C | I | I | R/A |
| تطوير Oracle Connector | C | R/A | C | I | I |
| اختبار القبول | R/A | C | C | I | C |
| إطلاق الإنتاج | A | C | C | R | C |

> R = مسؤول (Responsible), A = مُعتمِد (Accountable), C = مُستشار (Consulted), I = مُطّلع (Informed)

### 17.2 Approval Sign-off

| الدور | الاسم | التاريخ | التوقيع |
|-------|------|---------|---------|
| Product Owner | _________________ | ____/____/2026 | _________ |
| Technical Lead | _________________ | ____/____/2026 | _________ |
| Security Lead | _________________ | ____/____/2026 | _________ |
| CTO | _________________ | ____/____/2026 | _________ |
| Customer Representative | _________________ | ____/____/2026 | _________ |

---

## 18. Constraints & Dependencies (القيود والتبعيات)

### 18.1 Technical Constraints (قيود تقنية)

| # | القيد | التأثير | التخفيف |
|---|------|---------|---------|
| C1 | Oracle Connector يدعم SELECT فقط — لا يمكن تنفيذ INSERT/UPDATE/DELETE | المستخدمون لا يمكنهم تعديل البيانات عبر Atlas | مخطط لـ Q2 2026 مع workflow موافقات |
| C2 | `python-oracledb` Thin Mode لا يدعم جميع ميزات Oracle المتقدمة | بعض أنواع البيانات أو الميزات قد لا تعمل | توثيق القيود، التحول إلى Thick Mode عند الحاجة |
| C3 | الكلمات المحجوزة في SQL تُحظر حتى داخل النصوص (string literals) | استعلامات تحتوي كلمات مثل "DELETE" في نص قد تُرفض | قيد أمني مقصود (conservative approach) |
| C4 | Qdrant يعمل كنسخة واحدة (single instance) | نقطة فشل واحدة للبحث الدلالي | مخطط لـ cluster mode في Q2 |
| C5 | نموذج Qwen/Unsloth يتطلب GPU للأداء الأمثل | تكلفة أعلى للأجهزة | 4-bit quantization يقلل المتطلبات |

### 18.2 External Dependencies (تبعيات خارجية)

| # | التبعية | المزود | التأثير عند عدم التوفر | البديل |
|---|--------|--------|----------------------|--------|
| D1 | Alibaba Cloud (Riyadh Region) | Alibaba | توقف كامل | خطة DR في منطقة بديلة |
| D2 | Oracle Database (عميل) | العميل | عدم إمكانية الاستعلام | رسائل خطأ واضحة، باقي النظام يعمل |
| D3 | Claude API (Anthropic) | Anthropic | فشل المزود الأساسي | Fallback إلى GPT-4o أو Qwen |
| D4 | OpenAI API (GPT-4o) | OpenAI | فشل المزود البديل | Fallback إلى Claude أو Qwen |
| D5 | `sentence-transformers` model | Hugging Face | فشل تحميل النموذج | نسخة محلية مخزنة مسبقاً |
| D6 | PyPI / npm packages | متعدد | فشل البناء | تثبيت إصدارات محددة + mirror محلي |

### 18.3 Regulatory Dependencies (تبعيات تنظيمية)

| # | التبعية | الجهة | الحالة |
|---|--------|------|--------|
| R1 | امتثال PDPL | SDAIA | ✅ متوافق — يتطلب مراجعة مستمرة |
| R2 | تصنيف البيانات NDMO | NDMO | ✅ مُطبّق — Policy V1 |
| R3 | سيادة البيانات (Data Sovereignty) | NCA | ✅ استضافة داخل الرياض |
| R4 | متطلبات القطاع المصرفي (إن وُجدت) | SAMA | ⏳ قيد التقييم لعملاء القطاع المالي |

### 18.4 Team Dependencies (تبعيات الفريق)

| الفريق | المسؤولية | الحد الأدنى للموارد |
|--------|----------|-------------------|
| Backend Development | FastAPI، Oracle Connector، RAG Pipeline | 2 مهندسين |
| Frontend Development | React SPA، UX/UI | 1 مهندس |
| DevOps / Infrastructure | ACK، CI/CD، مراقبة | 1 مهندس |
| Security & Compliance | PDPL، تدقيق، اختبارات اختراق | 1 متخصص (دوام جزئي) |
| Customer Success | تأهيل، تدريب، دعم | 1 لكل 5 عملاء |

---

## Appendix A: Code Structure

```
src/atlas/
├── core/
│   ├── mzx_protocol.py            # MZX Identity: signature engine, base model, @mzx_signed
│   ├── config.py                  # AtlasConfig loader (mzx_config.yaml)
│   └── logging.py                 # MZX-aware structured JSON logging
├── agents/
│   └── atlas_agent.py             # AtlasAgent: tool registry, intent classification, MZX-signed
├── api/
│   ├── main.py                    # FastAPI app, /health, /v1/chat, /v1/security
│   ├── mcp_server.py              # MCP protocol server (/mcp/*)
│   ├── routes/
│   │   ├── auth.py                # /api/auth/* endpoints
│   │   ├── audit.py               # /api/audit/* endpoints
│   │   └── enterprise.py          # /api/enterprise/audit (Wafer ERP bridge)
│   └── security/
│       ├── auth.py                # JWT + bcrypt authentication
│       ├── models.py              # Pydantic models, RBAC roles
│       ├── audit.py               # Append-only audit logging
│       └── middleware.py          # Rate limiting, security headers
├── connectors/
│   ├── oracle/
│   │   ├── connector.py           # OracleConnector: validate_query() + execution
│   │   └── indexer.py             # OracleSchemaIndexer: Qdrant semantic search
│   └── picsellia.py               # Picsellia dataset/asset connector (optional)
├── agent/
│   ├── sql_agent.py               # OracleSQLAgent: NL-to-SQL RAG pipeline
│   └── unsloth_llm.py            # Qwen model via Unsloth (4-bit)
├── tools/                         # Enterprise data tools (CV tools moved to SelectX)
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
