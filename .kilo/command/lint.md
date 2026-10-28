---
description: Run ruff, mypy, eslint, tsc
---
Run all linters and type checkers across the backend and frontend.

```bash
# Backend
ruff check src
mypy src

# Frontend
cd web && npm run lint && npm run typecheck
```
