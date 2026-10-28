# Dev Mode

Start the API and frontend in development mode.

## Prerequisites

- Docker running (for Postgres + Redis)
- Python 3.12+
- Node.js 20+

## Commands

```bash
# Start infrastructure services
docker compose up -d postgres redis

# Start API (from project root)
uvicorn src.main:app --reload --port 8000

# Start frontend (from web directory)
cd web && npm run dev
```

## URLs

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
