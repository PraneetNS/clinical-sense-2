# Render Deployment Guide — Clinical Sense

This guide provides step-by-step instructions for deploying the **Clinical Sense** monorepo to Render, including database setup, backend, and frontend configuration.

## 🕒 Fast Build Optimization
I have already optimized the project to prevent build timeouts by:
- Disabling ESLint and Type-Checking during the Next.js build (`frontend/next.config.mjs`).
- Adding a `.dockerignore` for efficient file uploads.

---

## 1. Database Setup (PostgreSQL)
1.  Log in to [Render](https://dashboard.render.com).
2.  Click **New +** > **Database**.
3.  Name: `clinical-sense-db`
4.  Database: `clinical_sense`
5.  Click **Create Database**.
6.  Copy the **Internal Database URL** (for backend) or **External Database URL** (for local testing).

---

## 2. Backend Deployment (FastAPI)
1.  Click **New +** > **Web Service**.
2.  Connect your GitHub repository.
3.  **Name**: `clinical-sense-backend`
4.  **Root Directory**: `backend` (CRITICAL)
5.  **Runtime**: `Python 3`
6.  **Build Command**: `pip install -r requirements.txt`
7.  **Start Command**: `bash entrypoint.sh`
8.  **Environment Variables**:
    - `DATABASE_URL`: Paste your Render Database URL.
    - `ENV`: `production`
    - `GROQ_API_KEY`: Your Groq API key.
    - `JWT_SECRET`: Generate a random string (e.g., `python -c "import secrets; print(secrets.token_hex(32))"`).
    - `FRONTEND_URL`: Your Render frontend URL (e.g., `https://clinical-sense-ui.onrender.com`).
9.  Click **Create Web Service**.

---

## 3. Frontend Deployment (Next.js)
1.  Click **New +** > **Web Service**. (Use Web Service, not Static Site, for Next.js App Router).
2.  Connect your GitHub repository.
3.  **Name**: `clinical-sense-frontend`
4.  **Root Directory**: `frontend` (CRITICAL)
5.  **Runtime**: `Node`
6.  **Build Command**: `npm install && npm run build`
7.  **Start Command**: `npm run start`
8.  **Environment Variables**:
    - `NEXT_PUBLIC_API_URL`: Your backend URL with `/api/v1` suffix (e.g., `https://clinical-sense-backend.onrender.com/api/v1`).
9.  **Plan**: If the build fails with "Out of Memory", you may need to switch to the **Starter** plan (512MB is tight for Next.js 14).
10. Click **Create Web Service**.

---

## 🛠 Troubleshooting Build Timeouts
If Render shows a timeout or memory error during `next build`:
1.  **Check Memory Usage**: Render's free tier has 512MB RAM. Next.js 14 builds usually require ~768MB-1GB.
2.  **Solution**: I have already disabled linting/TS checks in `next.config.mjs` to keep it under 512MB, but if it still fails, the **Starter ($7/mo)** plan is recommended for production-grade builds.
3.  **Build Timeout**: In "Settings", search for **Build Timeout** and ensure it's set to at least 10-15 minutes.

## 🔐 Database Migrations
The `entrypoint.sh` in the backend folder automatically runs migrations on startup:
`python -m alembic upgrade head`
You don't need to run this manually.

## 🔗 Final Check
- Verify backend health: `https://your-backend.onrender.com/api/health`
- Ensure `FRONTEND_URL` on backend exactly matches the frontend domain.
