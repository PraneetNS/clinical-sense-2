# Clinical Documentation Assistant - Deployment Guide

## Prerequisites

- **Backend**: Railway or Render account
- **Frontend**: Vercel account
- **Database**: PostgreSQL instance (Railway/Render/Supabase/etc.)
- **API Keys**: At least one AI provider (Groq or OpenAI)

---

## Backend Deployment (Railway/Render)

### 1. Database Setup

Create a PostgreSQL database and obtain the connection string:
```
postgresql://user:password@host:port/dbname
```

### 2. Environment Variables

Set the following environment variables in your Railway/Render dashboard:

```bash
ENV=production
JWT_SECRET=<generate-secure-random-string>
DATABASE_URL=<your-postgresql-connection-string>
FRONTEND_URL=<your-vercel-frontend-url>
GROQ_API_KEY=<your-groq-api-key>
# OR
OPENAI_API_KEY=<your-openai-api-key>
```

**Generate JWT_SECRET**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Deploy

**Railway**:
- Connect your GitHub repository
- Railway will auto-detect the `Procfile`
- Deployment starts automatically

**Render**:
- Create a new Web Service
- Connect your repository
- Build Command: `pip install -r requirements.txt`
- Start Command: `bash entrypoint.sh`

### 4. Run Migrations

Migrations run automatically via `entrypoint.sh`. To run manually:
```bash
python -m alembic upgrade head
```

### 5. Verify Backend

Check health endpoint:
```
https://your-backend-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## Frontend Deployment (Vercel)

### 1. Environment Variables

In Vercel project settings, add:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app/api/v1
```

### 2. Deploy

- Import your GitHub repository to Vercel
- Vercel auto-detects Next.js
- Deployment starts automatically

### 3. Verify Frontend

- Visit your Vercel URL
- Login should work
- Patient CRUD operations should function
- PDF generation should work

---

## Post-Deployment Checklist

- [ ] Backend `/health` endpoint returns `healthy`
- [ ] Frontend loads without errors
- [ ] Login/registration works
- [ ] Patient creation works
- [ ] Clinical note generation works
- [ ] PDF report download works
- [ ] No console errors in browser
- [ ] No server errors in logs
- [ ] CORS is properly configured
- [ ] All secrets are set correctly

---

## Security Notes

1. **Never commit secrets** to version control
2. **JWT_SECRET** must be a cryptographically secure random string in production
3. **CORS** is automatically configured to allow only your frontend URL
4. **API docs** are disabled in production (`/docs` and `/redoc` return 404)
5. **Rate limiting** is active on all endpoints
6. **Request size limits** prevent resource exhaustion (10MB max)

---

## Troubleshooting

### Backend won't start
- Check all required environment variables are set
- Verify DATABASE_URL is correct
- Check logs for missing secrets error

### Frontend can't connect to backend
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS settings (FRONTEND_URL must match Vercel URL)
- Ensure backend is running

### Database connection fails
- Verify PostgreSQL connection string format
- Check database is accessible from backend host
- Ensure migrations have run

### AI features not working
- Verify at least one API key (GROQ_API_KEY or OPENAI_API_KEY) is set
- Check API key is valid
- Review backend logs for API errors

---

## Monitoring

### Backend Logs
- Railway: View in dashboard
- Render: View in dashboard

### Frontend Logs
- Vercel: View in dashboard under "Deployments"

### Structured Logging
All backend logs include:
- `request_id`: Unique identifier for each request
- `user_id`: Authenticated user (if applicable)
- `timestamp`: ISO 8601 format
- `level`: INFO, WARNING, ERROR

---

## Scaling Considerations

1. **Database**: Connection pooling is configured (20 connections, 10 overflow)
2. **File Uploads**: Stored locally (consider S3/CloudFlare R2 for production scale)
3. **Rate Limiting**: Configured per-IP (consider Redis for distributed systems)

---

## Support

For issues, check:
1. Backend logs for errors
2. Frontend console for client errors
3. `/health` endpoint status
4. Environment variable configuration
