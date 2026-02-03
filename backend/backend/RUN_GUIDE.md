# Running the Backend - Complete Guide

## 🚀 Quick Start

### Option 1: Development Mode (Recommended for Local)
```bash
cd backend
python -m app.main
```
This uses the built-in development server with auto-reload.

### Option 2: Using uvicorn directly
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option 3: Production-like with gunicorn (Testing)
```bash
cd backend
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
```

---

## 📦 First-Time Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
python -m alembic upgrade head

# 6. Create initial admin user (optional)
python seed_user.py

# 7. Start the server
python -m app.main
```

---

## 🔧 Development Commands

### Start Development Server
```bash
# Method 1: Direct Python execution (auto-reload enabled)
python -m app.main

# Method 2: Using uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Method 3: Custom port
uvicorn app.main:app --reload --host 127.0.0.1 --port 5000
```

### Database Operations
```bash
# Run migrations
python -m alembic upgrade head

# Create new migration
python -m alembic revision --autogenerate -m "description"

# Rollback one migration
python -m alembic downgrade -1

# Check current migration
python -m alembic current
```

### Testing Configuration
```bash
# Verify environment variables
python -c "from app.core.config import settings; print(f'ENV: {settings.ENV}'); print(f'DB: {settings.DATABASE_URL}')"

# Test database connection
python -c "from app.db.session import SessionLocal; db = SessionLocal(); print('DB Connected!'); db.close()"
```

---

## 🏭 Production Deployment

### Render/Railway (Automatic)
The `entrypoint.sh` script handles everything:
```bash
bash entrypoint.sh
```

This will:
1. Run database migrations
2. Start gunicorn with 4 uvicorn workers
3. Bind to `0.0.0.0:$PORT`

### Manual Production Start
```bash
# With environment variable PORT
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:$PORT

# With specific port
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Worker Count Recommendations
- **1 CPU**: 2 workers
- **2 CPUs**: 4 workers (default)
- **4 CPUs**: 8 workers
- **Formula**: `(2 x CPU cores) + 1`

To adjust, edit `entrypoint.sh`:
```bash
gunicorn app.main:app --workers 8 ...
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows: Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

### Import Errors
```bash
# Ensure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors
```bash
# Reset database (WARNING: deletes all data)
rm clinical_doc.db
python -m alembic upgrade head
python seed_user.py
```

### Environment Variable Issues
```bash
# Check if .env exists
ls .env

# Verify it's being loaded
python -c "from app.core.config import settings; print(settings.JWT_SECRET)"
```

---

## 📊 Monitoring

### Check Server Status
```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API docs (development only)
# Visit: http://localhost:8000/docs
```

### View Logs
Development mode shows logs in the terminal automatically.

For production (gunicorn):
- Logs are sent to stdout/stderr
- Access logs: `--access-logfile -`
- Error logs: `--error-logfile -`

---

## 🔐 Security Notes

### Development vs Production

**Development** (`python -m app.main`):
- Auto-reload enabled
- Runs on 127.0.0.1 (localhost only)
- API docs available at `/docs`
- Single worker

**Production** (`gunicorn`):
- No auto-reload
- Runs on 0.0.0.0 (all interfaces)
- API docs disabled
- Multiple workers for concurrency

### Never in Production
❌ `python -m app.main` (single worker, no load balancing)  
❌ `uvicorn` without gunicorn (single process)  
❌ `--reload` flag (performance overhead)  
❌ Development secrets in `.env`

### Always in Production
✅ `gunicorn` with uvicorn workers  
✅ Multiple workers (4+)  
✅ Secure JWT_SECRET  
✅ PostgreSQL database  
✅ HTTPS/SSL termination  

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start dev server | `python -m app.main` |
| Start with uvicorn | `uvicorn app.main:app --reload` |
| Start production-like | `gunicorn app.main:app -k uvicorn.workers.UvicornWorker` |
| Run migrations | `python -m alembic upgrade head` |
| Create admin user | `python seed_user.py` |
| Check health | `curl http://localhost:8000/health` |
| View API docs | Visit `http://localhost:8000/docs` |

---

## 📝 Notes

- The FastAPI app is defined in `app/main.py` as `app`
- No hardcoded host/port in the application code
- Development entry point is wrapped in `if __name__ == "__main__":`
- Production uses gunicorn to import and run the app
- All configuration comes from environment variables
