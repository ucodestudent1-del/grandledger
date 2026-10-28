# GrandLedger

A multi-tenant, audit-ready double-entry bookkeeping SaaS built with FastAPI + Next.js.

## Features

- **Immutable ledger** with draft → posted → void workflow
- **Double-entry invariant** enforced at the database level (Postgres trigger)
- **Sales (AR)**: Customers, invoices, credit notes, payments
- **Purchases (AP)**: Vendors, bills, debit notes, vendor payments
- **Banking**: Bank accounts, CSV import, transaction matching, reconciliation
- **Reports**: P&L, Balance Sheet, Trial Balance, General Ledger, AR/AP Aging
- **Multi-tenancy**: Row-level tenant isolation with company-scoped data
- **Audit log**: Immutable audit trail for every ledger mutation
- **Auth**: JWT access + rotating refresh tokens, RBAC (owner, accountant, bookkeeper, read-only)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12, SQLModel, Alembic |
| Database | PostgreSQL 16 (prod), SQLite (dev) |
| Cache | Redis 7 |
| Background Jobs | RQ (Redis Queue) |
| Auth | JWT (HS256), bcrypt |
| PDF | WeasyPrint |

## Quick Start

```bash
# Clone and setup
cp .env.example .env

# Start infrastructure
docker compose up -d postgres redis

# Run migrations
alembic upgrade head

# Seed demo data
python -m src.seeds

# Start API
uvicorn src.main:app --reload --port 8000

# Start frontend
cd web && npm install && npm run dev
```

## URLs

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Demo Credentials

```
Email: demo@grandledger.com
Password: password123
```

## Architecture

- **Single posting function**: All GL writes go through `services/posting.py`
- **Database invariant**: Postgres trigger `enforce_balanced_entry` ensures debits = credits
- **Tenant isolation**: Every tenant table has `company_id`; middleware enforces context
- **No floats**: `Decimal` in Python, `numeric(20,4)` in DB

## API

OpenAPI 3.1 docs at `/docs` (Swagger UI) and `/redoc` (ReDoc).

All endpoints are at `/api/v1/` and require a Bearer JWT token.

## Development

```bash
# Run all tests
pytest tests/ -v

# Lint + typecheck
ruff check src tests
mypy src
```

## Production Deployment

The frontend and API are bundled into a single Docker image. The Next.js frontend is
built as a static export during Docker build and served directly from FastAPI at `/`.

```bash
# Build and run the unified image
docker build -t grandledger .
docker run -p 8000:8000 --env-file .env grandledger

# Or with docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

Set `FRONTEND_URL` to the deployed application URL (e.g. `https://grandledger.up.railway.app`).

## License

MIT
