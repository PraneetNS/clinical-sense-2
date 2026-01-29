#!/bin/bash
set -e

echo "Starting Clinical Documentation Assistant Deployment Pipeline..."

# 1. Backend Setup
echo "--- Backend: Installing dependencies ---"
cd backend
python -m pip install -r requirements.txt

echo "--- Backend: Running database migrations ---"
python -m alembic upgrade head

# 2. Frontend Setup
echo "--- Frontend: Installing dependencies ---"
cd ../frontend
npm install

echo "--- Frontend: Building for production ---"
npm run build

echo "Deployment preparation complete."
echo "To start services:"
echo "Backend: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "Frontend: cd frontend && npm run start"
