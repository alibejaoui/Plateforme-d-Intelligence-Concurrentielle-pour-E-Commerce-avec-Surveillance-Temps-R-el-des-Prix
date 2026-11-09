#!/usr/bin/env sh
set -e

echo "[backend] running migrations (best-effort)..."
alembic upgrade head || echo "[backend] alembic upgrade failed (continuing)"

echo "[backend] starting uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
