---
description: Start Postgres + Redis via Docker Compose
---
Start the required Docker services for development.

```bash
docker compose up -d postgres redis
```

Wait for services to be healthy before running migrations or starting the API.
