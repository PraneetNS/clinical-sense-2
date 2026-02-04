# FINAL DEPLOYMENT CHECKLIST

## 1. Environment Variables
### Backend (Render)
- `ENV`: `production`
- `DATABASE_URL`: `postgresql://clinical_sense_user:KpEPHbhShfvI0dfjGN7rCHHaInlu5ZPX@dpg-d5tks514tr6s73b93odg-a/clinical_sense` (Internal URL)
- `JWT_SECRET`: (Generate a long random string)
- `FRONTEND_URL`: `https://clinical-sense.vercel.app` (Or your Vercel URL)
- `BACKEND_CORS_ORIGINS`: `["https://clinical-sense.vercel.app"]`
- `OPENAI_API_KEY` or `GROQ_API_KEY`: (If using AI)

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL`: `https://clinical-sense.onrender.com/api/v1`

## 2. Render Services config
- **Build Command**: `./render_build.sh` (or `pip install -r requirements.txt`)
- **Start Command**: `./entrypoint.sh` (Runs migrations + Gunicorn)
- **Root Directory**: `backend` (Recommended if you deployed the whole repo)

## 3. Verification
- Logs: Check Render logs for "✅ Database connection established".
- Health: Visit `/api/health` -> `{"status": "healthy"}`.
- DB: Visit `/api/health/db` -> `{"db": "connected"}`.
- Login: Frontend should log in without "Network Error" or 502.
