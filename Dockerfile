FROM --platform=linux/amd64 node:22-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY analysis-engine/requirements.txt ./analysis-engine/requirements.txt

RUN python3 -m venv /app/analysis-engine/.venv \
    && /app/analysis-engine/.venv/bin/pip install --no-cache-dir \
        --upgrade pip setuptools wheel \
    && /app/analysis-engine/.venv/bin/pip install --no-cache-dir \
        -r /app/analysis-engine/requirements.txt

COPY backend/package.json backend/package-lock.json ./backend/

WORKDIR /app/backend

RUN npm ci

WORKDIR /app

COPY analysis-engine ./analysis-engine
COPY backend ./backend

WORKDIR /app/backend

RUN npx prisma generate
RUN npm run build

ENV NODE_ENV=production
ENV PORT=10000
ENV ANALYSIS_ENGINE_PATH=/app/analysis-engine
ENV PYTHON_EXECUTABLE=/app/analysis-engine/.venv/bin/python

EXPOSE 10000

CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]