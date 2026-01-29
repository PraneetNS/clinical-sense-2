#!/bin/bash
# Exit on error
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application..."
# Port is provided by environment ($PORT)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
