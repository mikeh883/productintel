#!/usr/bin/env bash
set -euo pipefail

# Apply migrations before serving (ADR 0008).
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
