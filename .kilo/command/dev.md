---
description: Start API + frontend in dev mode (Docker services already running)
---
Start the API (uvicorn) and frontend (Next.js dev) in dev mode.

API:
```
cd web/.. && uvicorn src.main:app --reload --port 8000
```

Frontend:
```
cd web && npm run dev
```

Run both in parallel or in separate terminals. The API serves docs at `http://localhost:8000/docs` and the frontend at `http://localhost:3000/`.
