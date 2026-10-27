# AGENTS.md — GrandLedger Bookkeeping SaaS

**Project:** GrandLedger — a multi-tenant double-entry bookkeeping SaaS MVP.
**Working dir:** `C:\Users\New User\Desktop\GrandLedger`
**Today:** 2026-10-26

---

## 1. Vision & Scope

GrandLedger is a bookkeeping SaaS for freelancers, small businesses, and accountants managing multiple clients. The **MVP** ships with a correct, audit-ready double-entry ledger and the core workflows needed to record transactions and produce standard financial statements.

### 1.1 MVP In-Scope

| Area | Features |
|---|---|
| **Ledger core** | Chart of accounts (default COA + custom), immutable journal entries, draft → posted workflow, reversal-based corrections, period locking, numeric money (`numeric(20,4)`), debit/credit invariant enforced in DB. |
| **Sales (AR)** | Customers, invoices (draft → issued → void), invoice PDF, payments (full + partial), credit notes, payment terms, AR aging report. |
| **Purchases (AP)** | Vendors, bills (draft → posted → void), vendor payments (full + partial), debit notes, AP aging report. |
| **Banking** | Bank accounts, CSV import, transaction matching, reconciliation screen. |
| **Reports** | Profit & Loss, Balance Sheet, Trial Balance, General Ledger, Cash Summary. |
| **Multi-tenancy** | Row-level tenant isolation (company-scoped data), tenant context middleware. |
| **Users & Auth** | Sign up / login (email+password), JWT access + rotating refresh tokens, accountant invite flow (role: accountant), owner/bookkeeper/read-only roles. |
| **Audit** | Immutable audit log for every ledger mutation (user, IP, timestamp, before/after). |
| **DevOps** | Docker Compose (Postgres, Redis, API, Web), Alembic migrations, CI lint+test, local SQLite for dev. |

### 1.2 Out of Scope (Post-MVP)

- Payroll, fixed assets, inventory, multi-currency, budgeting, bank feeds API, tax e-filing, AI features, desktop/mobile apps, consolidated reports across companies.

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Frontend** | Next.js 15 App Router, React 19, TypeScript | SSR + App Router, server components, Vercel-ready. |
| **Design** | Tailwind CSS v4, shadcn/ui | Rapid, accessible, themeable. |
| | TanStack Table / AG Grid | Accountant-grade data grids. |
| | TanStack Query | Cache + background sync of ledger data. |
| **Backend** | FastAPI, Python 3.11+, SQLModel, Alembic | Type-safe, fast dev, async, great docs (OpenAPI auto-gen). |
| **Database** | PostgreSQL 16 (prod), SQLite (dev) | `numeric(20,4)` money handling, row-level security support, maturity. |
| **Cache / Queues** | Redis 7 | Session store, background jobs, reconciliation cache. |
| **Tasks** | RQ (Redis Queue) or Celery | Bank import, PDF/email generation off the request thread. |
| **Auth** | JWT (HS256) access + rotating refresh, bcrypt, httpOnly + CSRF double-submit | Industry standard, accountant-safe. |
| **Money** | `decimal.Decimal` in Python, `numeric(20,4)` in DB — never floats | Avoid floating-point drift. |
| **PDF** | WeasyPrint (server) | Invoice/statement PDFs from HTML templates. |
| **Hosting** | AWS or GCP, Terraform IaC, GitHub Actions CI | SOC 2 Type II path. |
| **Frontend deploy** | Vercel | Fast iteration. |
| | Backend deploy | Railway / Fly.io (MVP) → ECS / Cloud Run (scale). |

### 2.1 Key Architectural Decisions

1. **Immutable ledger:** Posted journal lines are never updated. Corrections = reversing entry + new entry. Audit trail is inherent.
2. **Invariant in the database:** A Postgres trigger / `check`/transaction enforces `SUM(debits) = SUM(credits)` per journal entry before commit. Application code is secondary.
3. **Single posting function:** All GL writes go through one function (`services/posting.py`) to centralize the invariant.
4. **Row-level tenancy:** Every tenant-scoped table has `company_id`; middleware sets the tenant context. RLS policies as defense-in-depth.
5. **No floats:** `Decimal` everywhere; `numeric(20,4)` in DB.

---

## 3. Data Model (MVP)

```
Company
├─ id (uuid pk)
├─ name, slug, currency
├─ financial_year_start (date)
├─ created_at, updated_at

User
├─ id, company_id, email, name, role [owner|accountant|bookkeeper|readonly]
├─ password_hash, is_external_accountant
└─ created_at

Account (Chart of Accounts)
├─ id, company_id, code, name, type [asset|liability|equity|revenue|expense]
├─ parent_id (tree), is_active, is_system
└─ created_at

JournalEntry
├─ id, company_id, number (JE-YYYY-00001)
├─ entry_date, description, status [draft|posted|void]
├─ posted_at, posted_by (user_id)
├─ is_closed_period (bool, period lock check)
└─ created_at, updated_at, created_by

JournalLine
├─ id, journal_entry_id
├─ account_id, description
├─ debit (numeric 20,4), credit (numeric 20,4)  -- one is 0
└─ created_at

AuditLog
├─ id, company_id, user_id, action, entity_type, entity_id
├─ before (jsonb), after (jsonb), ip_address
└─ created_at

Contact (Customer / Vendor — shared)
├─ id, company_id, name, type [customer|vendor]
├─ email, phone, address (json)
└─ created_at

Invoice
├─ id, company_id, contact_id (customer)
├─ number, status [draft|issued|void|paid]
├─ issue_date, due_date, subtotal, tax_total, total
├─ currency, exchange_rate
└─ created_at, updated_at

InvoiceLine
├─ id, invoice_id, description, qty, unit_price, tax_rate, amount
└─ account_id (revenue/expense mapping)

Payment / Receipt
├─ id, company_id, contact_id
├─ type [payment|receipt], amount, payment_date
├─ allocated_to (json: [{invoice_id, amount}])
└─ journal_entry_id (the JE that posts this payment)

BankAccount
├─ id, company_id, name, bank_name, account_number
└─ starting_balance, currency

BankTransaction
├─ id, company_id, bank_account_id
├─ date, description, amount, balance
├─ imported_at, matched (bool), journal_entry_id (nullable)
└─ status [pending|cleared|reconciled]

File
├─ id, company_id, url, filename, content_type, size
└─ uploaded_at
```

### 3.1 Journal Entry Invariant Trigger (Postgres)

```sql
-- Prevent debit != credit on posted entries
CREATE OR REPLACE FUNCTION enforce_balanced_entry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'posted' THEN
        IF (SELECT COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0)
            FROM journal_lines WHERE journal_entry_id = NEW.id) <> 0 THEN
            RAISE EXCEPTION 'Journal entry % is not balanced (debits != credits)', NEW.id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER balanced_entry_trigger
BEFORE UPDATE ON journal_entries
FOR EACH ROW EXECUTE FUNCTION enforce_balanced_entry();
```

---

## 4. API Design

REST API at `/api/v1/`, OpenAPI 3.1 auto-generated by FastAPI + Redoc/Swagger UI.

### 4.1 Routes

| Module | Endpoints |
|---|---|
| **Auth** | `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` |
| **Companies** | `POST /companies`, `GET /companies`, `GET /companies/{id}` |
| **Accounts** | `GET /accounts`, `POST /accounts`, `GET /accounts/{id}`, `PATCH /accounts/{id}` |
| **Journals** | `GET /journals`, `POST /journals`, `GET /journals/{id}`, `POST /journals/{id}/post`, `POST /journals/{id}/void`, `POST /journals/{id}/reverse` |
| **Contacts** | `GET /contacts`, `POST /contacts`, `GET /contacts/{id}` |
| **Invoices** | `GET /invoices`, `POST /invoices`, `GET /invoices/{id}`, `POST /invoices/{id}/issue`, `POST /invoices/{id}/void`, `GET /invoices/{id}/pdf` |
| **Payments** | `GET /payments`, `POST /payments`, `GET /payments/{id}` |
| **Bills** | `GET /bills`, `POST /bills`, `GET /bills/{id}`, `POST /bills/{id}/post`, `POST /bills/{id}/void` |
| **Bank** | `GET /bank/accounts`, `POST /bank/transactions/import`, `GET /bank/transactions`, `POST /bank/transactions/{id}/match` |
| **Reports** | `GET /reports/profit-loss`, `GET /reports/balance-sheet`, `GET /reports/trial-balance`, `GET /reports/general-ledger`, `GET /reports/ar-aging`, `GET /reports/ap-aging` |
| **Audit** | `GET /audit/logs` |

All endpoints require JWT bearer token. Tenant context derived from the user's active company (or company slug).

---

## 5. Frontend Structure (Next.js App Router)

```
web/
├── app/
│   ├── (auth)/              -- login, signup (unauthenticated)
│   │   ├── layout.tsx
│   │   └── login/
│   │       └── page.tsx
│   │   └── signup/
│   │       └── page.tsx
│   ├── app/                  -- main authenticated layout
│   │   ├── layout.tsx        -- sidebar + header
│   │   ├── page.tsx          -- dashboard
│   │   ├── (ar)/
│   │   │   ├── customers/
│   │   │   │   └── [id]/
│   │   │   └── invoices/
│   │   │       └── [id]/
│   │   │           └── pdf/
│   │   ├── (ap)/
│   │   │   ├── vendors/
│   │   │   └── bills/
│   │   │       └── [id]/
│   │   ├── (bank)/
│   │   │   ├── accounts/
│   │   │   └── reconcile/
│   │   │       └── [id]/
│   │   ├── accounting/
│   │   │   ├── chart-of-accounts/
│   │   │   └── journals/
│   │   │       └── [id]/
│   │   ├── reports/
│   │   │   ├── profit-loss/
│   │   │   ├── balance-sheet/
│   │   │   ├── trial-balance/
│   │   │   ├── general-ledger/
│   │   │   ├── ar-aging/
│   │   │   └── ap-aging/
│   │   ├── audit/
│   │   └── settings/
│   │       ├── company/
│   │       └── users/
│   ├── components/           -- Sidebar, Header, shared UI
│   ├── lib/
│   │   ├── api.ts            -- ky + TanStack Query API client
│   │   └── utils.ts
│   ├── hooks/
│   ├── types/
│   │   └── api.ts            -- TypeScript API types
│   └── styles/
│       └── globals.css
```

Design system: Tailwind + shadcn/ui components. Shared components in `components/` (DataTable, FormDrawer, StatusBadge). API client: `lib/api.ts` using `ky` + `@tanstack/react-query`.

---

## 6. Backend Structure (FastAPI)

```
src/
  main.py                  -- FastAPI app, middleware, CORS
  config.py                -- Pydantic settings (env-driven)
  database.py              -- engine, session, SQLModel registry
  models/                  -- SQLModel ORM models (see §3)
  schemas/                 -- Pydantic request/response DTOs
  api/
    v1/
      __init__.py
      auth.py
      companies.py
      accounts.py
      journals.py
      contacts.py
      invoices.py
      payments.py
      bills.py
      banking.py
      reports.py
      audit.py
  core/
    security.py            -- JWT, bcrypt, password hashing
    middleware.py            -- tenant context, audit logging
  services/
    posting.py              -- the single GL posting function (invariant enforcer)
    reports.py              -- P&L, BS, TB, GL, aging
    banking.py              -- CSV parse + import
    pdf.py                  -- WeasyPrint invoice/statement render
  workers/                 -- RQ/Celery tasks (PDF, email, bank import)
  migrations/              -- Alembic
tests/
  unit/
  integration/
Dockerfile
docker-compose.yml
alembic.ini
```

### 6.1 The Posting Function (`services/posting.py`)

Central authority for all GL writes. Signature concept:

```python
def post_journal(
    company_id: UUID,
    lines: list[JournalLineCreate],
    description: str,
    entry_date: date,
    created_by: UUID,
    source: str,
) -> JournalEntry:
    """Create a draft journal entry, validate balance, return it."""
    ...
```

All Sales/Purchase/Payment features call this — never write `JournalLine` directly.

---

## 7. MVP Milestones (Roadmap)

Each milestone = one deployable slice + tests.

| # | Milestone | Deliverables |
|---|---|---|
| **1** | Scaffold & ledger core | Monorepo scaffold, Docker compose, Postgres/SQLite, SQLModel models, Alembic baseline, JWT auth, company + account CRUD, journal entry CRUD with draft/post/void/reverse, balance trigger. |
| **2** | AR (invoicing + payments) | Customer CRUD, invoice CRUD (draft/issue/void), invoice PDF, payment receipt (full + partial), payment allocation, AR aging report. |
| **3** | AP (bills + payments) | Vendor CRUD, bill CRUD (post/void), bill payment, AP aging report. |
| **4** | Banking & reconciliation | Bank account CRUD, CSV import, transaction list, match-to-journal, reconciliation screen, clear/reconcile status. |
| **5** | Financial reports | P&L, Balance Sheet, Trial Balance, General Ledger, audit log viewer, period lock UI. |
| **6** | Hardening & deployment | Docker production compose, CI pipeline (lint+typecheck+test), env config, README, .kilo setup/run scripts, basic seeding. |

---

## 8. Development Workflow

### 8.1 Setup

```bash
# One-time
cp .env.example .env
# .env sets DATABASE_URL, REDIS_URL, SECRET_KEY, etc.

# Start services
docker compose up -d postgres redis
# API (dev, hot reload)
uvicorn src.main:app --reload --port 8000
# Frontend (dev)
cd web && npm run dev   # http://localhost:3000
```

### 8.2 Database

```bash
# Make a migration
alembic revision --autogenerate -m "description"
alembic upgrade head

# Dev seed (creates demo company + data)
python -m src.seeds
```

### 8.3 Testing

- **Unit tests:** `pytest tests/unit` (pytest, coverage)
- **Integration tests:** `pytest tests/integration` (TestClient + SQLite in-memory, or Postgres with Docker)
- **Type checking:** `mypy src`
- **Lint:** `ruff check src`
- **Frontend:** `npm run lint && npm run typecheck && npm test`

### 8.4 CI (GitHub Actions — `.github/workflows/ci.yml`)

- Lint: `ruff`, `mypy`
- Test: `pytest` with coverage threshold (≥80%)
- Frontend: `npm run lint && npm run typecheck && npm test`
- Build: Docker build + push on main

---

## 9. Quality & Compliance

| Requirement | How |
|---|---|
| **Debit = Credit invariant** | Postgres trigger (`enforce_balanced_entry`) + app-level validation. |
| **Immutable ledger** | No `UPDATE` on `posted` journal lines; corrections via reversal JV. |
| **Audit trail** | `audit_log` table populated via SQLAlchemy event hooks or explicit logging in `posting.py`. |
| **Tenant isolation** | All tenant tables filtered by `company_id`; middleware asserts context; optional RLS. |
| **Money safety** | `Decimal` types only; DB column `numeric(20,4)`. |
| **SOC 2 prep** | TLS 1.3, encrypted-at-rest, audit logging from day one; plan Vanta/Drata integration post-MVP. |
| **Error handling** | `HTTPException` with structured errors; no raw tracebacks to clients. |
| **Rate limiting** | SlowAPI (per-IP + per-user) on auth endpoints. |

---

## 10. Commands

Project commands live in `.kilo/command/`. Available commands:

| Command | Description |
|---|---|
| `/dev` | Start API + frontend in dev mode (Docker services already running). |
| `/test` | Run all tests (unit + integration). |
| `/lint` | Run ruff, mypy, eslint, tsc. |
| `/typecheck` | Run mypy + tsc only. |
| `/db-up` | Start Postgres + Redis via Docker Compose. |
| `/db-migrate` | Run `alembic upgrade head`. |
| `/db-seed` | Seed demo data. |
| `/build` | Build Docker images for API + frontend. |

Setup scripts for Agent Manager are in `.kilo/setup-script` (macOS/Linux) and `.kilo/setup-script.ps1` (Windows). Run scripts are in `.kilo/run-script` and `.kilo/run-script.ps1`.

---

## 11. Risk Register

| Risk | Mitigation |
|---|---|
| Ledger corruption from float math | Decimal-only, DB `numeric`, no float in money paths. |
| Unbalanced entries slipped through | DB trigger + single posting function. |
| Tenant data leak | Tenant middleware + row-level scoping + RLS. |
| Report performance | Pre-compute period balances; cache with Redis TTL; index on `entry_date`, `account_id`, `company_id`. |
| PDF generation blocking | Background task via RQ/Celery. |
| Auth bypass on multi-client access | RBAC checked per request in middleware; external accountant gets scoped access. |

---

## 12. References

- [Kanopy: How to Build a Bookkeeping App](https://kanopylabs.com/blog/how-to-build-a-bookkeeping-app)
- [dubbl](https://github.com/dubbl-org/dubbl) — open-source QuickBooks alternative
- [Easy-Books](https://github.com/Avishekdevnath/UrAccount-Solutions) — FastAPI + Next.js reference
- [ReQu](https://github.com/HarvzReQu/ReQu) — open cloud accounting, double-entry engine + AR/AP
