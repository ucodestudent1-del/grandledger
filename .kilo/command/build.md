# Build

Build the Docker image (multi-stage: builds the Next.js frontend and the Python API in one image).

```bash
docker build -t grandledger .
```

For local development compose:

```bash
docker compose build
```

For production:

```bash
docker build -t grandledger-prod .
```
