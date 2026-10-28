# Dev Mode

Start the API and frontend in development mode (separate processes).

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

# Start frontend dev server (from web directory)
cd web && npm run dev
```

## URLs

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend (dev server): http://localhost:3000

In development, the frontend dev server proxies API requests to the FastAPI backend via `NEXT_PUBLIC_API_URL`.

In production, the frontend is built into the Docker image and served directly from the API service at `/`.
