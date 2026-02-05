# Deployment Configuration Guide

## 1. Database Configuration (Render PostgreSQL)

You have been provided with two database connection strings. Use them as follows:

### **External Database URL** (For Local Development & Vercel)
Use this when running the app on your laptop or if Vercel needs to connect explicitly (though usually Frontend -> Backend -> DB).
```
postgresql://clinical_sense_user:KpEPHbhShfvI0dfjGN7rCHHaInlu5ZPX@dpg-d5tks514tr6s73b93odg-a.oregon-postgres.render.com/clinical_sense
```

### **Internal Database URL** (For Render Backend)
Use this within the Render "Environment Variables" settings for the fastest, most secure connection.
```
postgresql://clinical_sense_user:KpEPHbhShfvI0dfjGN7rCHHaInlu5ZPX@dpg-d5tks514tr6s73b93odg-a/clinical_sense
```

---

## 2. Environment Variables Checklist

### **Backend (Render)**
| Variable | Value |
|----------|-------|
| `DATABASE_URL` | *(Use Internal DB URL above)* |
| `JWT_SECRET` | *(Generate a strong secret)* |
| `ENV` | `production` |
| `FRONTEND_URL` | `https://clinical-sense.vercel.app` |

### **Frontend (Vercel)**
| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend-app.onrender.com/api/v1` |

## 3. Deployment Steps

1. **Push Code**: Commit and push your latest changes to GitHub.
2. **Render**: 
   - Triggers auto-deploy.
   - Ensure `Build Command` is `./deploy.sh`.
   - Ensure `Start Command` is `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`.
3. **Vercel**:
   - Triggers auto-deploy.
   - Verify the `VITE_API_URL` environment variable is set.

## 4. Verification
- Visit `https://your-backend-app.onrender.com/api/health/db` to confirm DB connection.
- Visit `https://clinical-sense.vercel.app/login` to test authentication.
