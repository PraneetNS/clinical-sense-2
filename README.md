# Clinical Documentation Assistant

A secure, production-ready AI-powered clinical documentation system built with FastAPI and Next.js.

## Features

- **AI-Powered Note Structuring**: Converts raw clinical notes into structured SOAP format using Groq/OpenAI
- **Patient Management**: Complete CRUD operations for patient records
- **Clinical Timeline**: Unified view of all patient clinical events
- **Case Status Management**: Track patient cases (Active/Closed) with audit logging
- **PDF Report Generation**: Comprehensive patient reports with timeline
- **Role-Based Access Control**: Admin, Clinician, and Staff roles
- **Audit Logging**: Full history tracking for all clinical notes
- **Security**: JWT authentication, rate limiting, input validation

## Tech Stack

**Backend**:
- FastAPI (Python)
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL (production) / SQLite (development)
- JWT authentication
- Groq/OpenAI integration

**Frontend**:
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Axios for API calls

## Quick Start (Development)

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional, uses SQLite by default)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum, set GROQ_API_KEY or OPENAI_API_KEY

# Run migrations
python -m alembic upgrade head

# Create initial user (optional)
python seed_user.py

# Start server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

### Quick Deploy Summary

**Backend (Railway/Render)**:
1. Set environment variables (ENV, JWT_SECRET, DATABASE_URL, FRONTEND_URL, GROQ_API_KEY)
2. Connect repository
3. Deploy (migrations run automatically)

**Frontend (Vercel)**:
1. Set NEXT_PUBLIC_API_URL
2. Connect repository
3. Deploy

## Environment Variables

### Backend (Required)
```bash
ENV=production
JWT_SECRET=<secure-random-string>
DATABASE_URL=<postgresql-connection-string>
FRONTEND_URL=<your-vercel-url>
GROQ_API_KEY=<your-groq-key>  # OR OPENAI_API_KEY
```

### Frontend (Required)
```bash
NEXT_PUBLIC_API_URL=<your-backend-url>/api/v1
```

## API Documentation

When running in development mode, API docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

In production, these endpoints are disabled for security.

## Security Features

- JWT-based authentication with configurable expiration
- Rate limiting (10 req/min for AI endpoints, 100 req/min global)
- Request size limits (10MB max)
- CORS restricted to frontend domain
- Input validation on all endpoints
- SQL injection prevention via ORM
- Path traversal protection for file uploads
- Structured logging with request IDs

## Project Structure

```
clinical-doc-assistant/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, security, logging
│   │   ├── db/           # Database session
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   ├── requirements.txt
│   └── Procfile          # Deployment config
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # API client
│   └── package.json
└── DEPLOYMENT.md         # Deployment guide
```

## License

Proprietary - All rights reserved

## Support

For deployment issues, see [DEPLOYMENT.md](./DEPLOYMENT.md) troubleshooting section.
