# GrandLedger Bookkeeping SaaS MVP

A multi-tenant double-entry bookkeeping SaaS built for freelancers, small businesses, and accountants managing multiple clients.

## Architecture

```
┌────────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Next.js 15 Web    │    │  FastAPI Backend │    │ PostgreSQL 16      │
│   (App Router,      │───▶│  (SQLModel,       │────│  (numeric(20,4)    │
│    TS, Tailwind,    │    │   Alembic)        │    │   money handling)  │
│    shadcn/ui)        │    │                   │    │                    │
├────────────────────┤    ├──────────────────┤    ├────────────────────┤
│   Redis 7           │    │  WeasyPrint       │    │  Docker Compose    │
│   (cache, RQ queue) │◀──▶│  (PDF generation) │    │  / Kubernetes      │
└────────────────────┘    └──────────────────┘    └────────────────────┘
```

## Key Design Decisions

1. **Immutable ledger**: Posted journal lines are never updated. Corrections are made via reversing entries + new entries.
2. **DB-enforced invariant**: A Postgres trigger ensures `SUM(debits) = SUM(credits)` on every journal entry.
3. **Single posting function**: All GL writes go through `src/services/posting.py`.
4. **Tenant isolation**: Every tenant-scoped table has `company_id`; middleware enforces context.
5. **Decimal-only money**: No floats anywhere — `Decimal` in Python, `numeric(20,4)` in DB.

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env if needed

# 2. Start services
docker compose up -d postgres redis

# 3. Run migrations
alembic upgrade head

# 4. Seed demo data
python -m src.seeds

# 5. Start API (dev)
uvicorn src.main:app --reload --port 8000

# 6. Start frontend (dev)
cd web && npm install && npm run dev
```

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Demo login: `demo@grandledger.com` / `password123`

## Project Structure

```
src/
├── main.py              # FastAPI app, middleware, CORS
├── config.py            # Pydantic settings (env-driven)
├── database.py          # SQLModel engine + session
├── models/              # ORM models
├── schemas/             # Pydantic DTOs
├── api/v1/              # REST endpoints
├── core/                # Security, middleware, tenant context
├── services/            # Posting, reports, PDF, banking
├── workers/             # RQ background tasks
└── migrations/          # Alembic
web/
├── app/                 # Next.js App Router
├── components/          # Shared UI components
├── lib/                 # API client, utilities
├── hooks/               # Custom React hooks
└── types/               # TypeScript types
```

## Development Commands

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `alembic upgrade head` | Apply database migrations |
| `python -m src.seeds` | Seed demo data |
| `uvicorn src.main:app --reload` | Start API in dev mode |
| `cd web && npm run dev` | Start frontend in dev mode |
| `pytest tests/` | Run all tests |

## License

See LICENSE file.
