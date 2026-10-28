# Database Migrate

Run Alembic migrations to apply the latest schema.

```bash
alembic upgrade head
```

To make a new migration:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
