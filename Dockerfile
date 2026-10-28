################################################################################
# Stage 1: Build the Next.js frontend (static export)
################################################################################
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund --legacy-peer-deps

COPY web/ ./
RUN npm run build

################################################################################
# Stage 2: Python API image with frontend static files baked in
################################################################################
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Next.js static export output
COPY --from=frontend-builder /app/out ./web/out

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
