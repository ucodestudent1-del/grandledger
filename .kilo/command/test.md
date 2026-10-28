---
description: Run all tests (unit + integration)
---
Run the full test suite with pytest, including unit and integration tests.

```bash
pytest tests/ -v
```

This uses SQLite in-memory by default for integration tests. For Postgres-based tests, set `DATABASE_URL` to a test database.
