#!/bin/bash
# Exit on error
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application with gunicorn + uvicorn workers..."
# Port is provided by environment ($PORT)
# Use 4 workers for production (adjust based on your server resources)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000} \
  --access-logfile - \
  --error-logfile - \
  --log-level info
