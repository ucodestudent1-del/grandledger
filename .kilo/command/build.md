# Build

Build Docker images for API and frontend.

```bash
docker compose build
```

For production builds:

```bash
docker build -t grandledger-api .
docker build -t grandledger-web ./web
```
