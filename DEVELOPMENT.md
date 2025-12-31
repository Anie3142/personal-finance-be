# NairaTrack Development & Deployment Guide

## 📁 Repository Structure

```
personal-finance-be/     # Django Backend
personal-finance-fe/     # Next.js Frontend
namesless-company-infra/ # Terraform Infrastructure
```

---

## 🖥️ Local Development (Docker)

### Prerequisites
- Docker Desktop installed
- Node.js 20+ (for running frontend outside Docker)
- Git

### Quick Start

```bash
# 1. Clone both repos
git clone git@github.com:Anie3142/personal-finance-be.git
git clone git@github.com:Anie3142/personal-finance-fe.git

# 2. Set up environment variables
cd personal-finance-be
cp .env.example .env
# Edit .env with your local values

cd ../personal-finance-fe
cp .env.example .env.local
# Edit .env.local with your Auth0 credentials

# 3. Start everything with Docker
cd ../personal-finance-be
docker compose up -d

# 4. Access the apps
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/api/v1/
```

### Docker Services

| Service | URL | Description |
|---------|-----|-------------|
| `frontend` | http://localhost:3000 | Next.js app |
| `api` | http://localhost:8000 | Django REST API |
| `db` | localhost:5432 | PostgreSQL database |

### Useful Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f
docker compose logs -f api
docker compose logs -f frontend

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up -d --build frontend
docker compose up -d --build api

# Access Django shell
docker compose exec api python manage.py shell

# Run migrations
docker compose exec api python manage.py migrate

# Create superuser
docker compose exec api python manage.py createsuperuser
```

### Running Frontend Locally (faster development)

```bash
# Stop Docker frontend
docker compose stop frontend

# Run frontend locally with hot reload
cd ../personal-finance-fe
npm run dev

# Frontend at http://localhost:3000
# Still connects to Docker backend at http://localhost:8000
```

---

## 🧪 Testing

### E2E Tests (Playwright)

```bash
cd personal-finance-fe

# Run all tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test export

# View test report
npx playwright show-report
```

### Backend Tests

```bash
cd personal-finance-be
docker compose exec api python manage.py test
```

### API Health Check

```bash
curl http://localhost:8000/api/v1/health
# {"status": "healthy", "version": "1.0.0", ...}
```

---

## 🚀 Production Deployment

### Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Cloudflare     │────▶│  Next.js (SSR)  │
│  Pages          │     │  personal-      │
│                 │     │  finance.       │
│                 │     │  nameless...    │
└─────────────────┘     └─────────────────┘
                               │
                               ▼
┌─────────────────┐     ┌─────────────────┐
│  AWS ALB/       │────▶│  Django API     │
│  Traefik        │     │  (ECS Fargate)  │
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  PostgreSQL     │
                        │  (AWS RDS)      │
                        └─────────────────┘
```

### Frontend → Cloudflare Pages

**Deployment:** Automatic via GitHub push to `main` branch

**Environment Variables (Cloudflare Dashboard):**
```
AUTH0_SECRET          = <from-aws-param-store-or-generate>
AUTH0_BASE_URL        = https://personal-finance.namelesscompany.cc
AUTH0_ISSUER_BASE_URL = https://dev-54nxe440ro81hlb6.auth0.com
AUTH0_CLIENT_ID       = <your-auth0-client-id>
AUTH0_CLIENT_SECRET   = <your-auth0-client-secret>
NEXT_PUBLIC_API_BASE_URL = https://api.personal-finance.namelesscompany.cc/api/v1
```

**Build Settings:**
- Build command: `npm run build`
- Output directory: `.next`
- Framework preset: Next.js

### Backend → AWS ECS

**Deployment:** Jenkins pipeline triggered by GitHub push to `main`

**AWS Parameter Store Keys:**
```
/nairatrack/prod/django/secret_key
/nairatrack/prod/db/host
/nairatrack/prod/db/port
/nairatrack/prod/db/name
/nairatrack/prod/db/user
/nairatrack/prod/db/password
/nairatrack/prod/auth0/domain
/nairatrack/prod/auth0/client_id
/nairatrack/prod/mono/secret_key
/nairatrack/prod/mono/public_key
```

**ECS Task Definition Environment:**
```json
{
  "environment": [
    {"name": "DJANGO_ENV", "value": "production"},
    {"name": "DEBUG", "value": "False"},
    {"name": "ALLOWED_HOSTS", "value": "api.personal-finance.namelesscompany.cc"}
  ],
  "secrets": [
    {"name": "SECRET_KEY", "valueFrom": "/nairatrack/prod/django/secret_key"},
    {"name": "DB_HOST", "valueFrom": "/nairatrack/prod/db/host"},
    {"name": "DB_PASSWORD", "valueFrom": "/nairatrack/prod/db/password"}
  ]
}
```

---

## 🔐 Environment Variables Reference

### Frontend (.env.local)

| Variable | Local | Production |
|----------|-------|------------|
| `AUTH0_SECRET` | Random 32+ chars | Same |
| `AUTH0_BASE_URL` | http://localhost:3000 | https://personal-finance.namelesscompany.cc |
| `AUTH0_ISSUER_BASE_URL` | https://dev-xxx.auth0.com | Same |
| `AUTH0_CLIENT_ID` | Your client ID | Same |
| `AUTH0_CLIENT_SECRET` | Your client secret | Same |
| `NEXT_PUBLIC_API_BASE_URL` | http://localhost:8000/api/v1 | https://api.personal-finance.namelesscompany.cc/api/v1 |

### Backend (.env)

| Variable | Local | Production |
|----------|-------|------------|
| `DJANGO_ENV` | development | production |
| `DEBUG` | True | False |
| `SECRET_KEY` | Any string | AWS Parameter Store |
| `DB_HOST` | db | RDS endpoint |
| `DB_PASSWORD` | localdevpassword | AWS Parameter Store |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | api.personal-finance.namelesscompany.cc |
| `CORS_ALLOWED_ORIGINS` | http://localhost:3000 | https://personal-finance.namelesscompany.cc |

---

## 📋 CI/CD Pipeline

### Frontend (Cloudflare Pages)

1. Push to `main` branch
2. Cloudflare detects change
3. Runs `npm run build`
4. Deploys to edge network
5. Available at production URL

### Backend (Jenkins → ECS)

1. Push to `main` branch
2. GitHub webhook triggers Jenkins
3. Jenkins runs:
   - `docker build`
   - `docker push` to ECR
   - `aws ecs update-service`
4. ECS pulls new image
5. Zero-downtime deployment

---

## 🐛 Troubleshooting

### Frontend not loading
```bash
# Check container status
docker compose ps

# View logs
docker compose logs frontend

# Rebuild
docker compose up -d --build frontend
```

### Backend 500 errors
```bash
# Check logs
docker compose logs api

# Check database connection
docker compose exec api python manage.py dbshell

# Run migrations
docker compose exec api python manage.py migrate
```

### Auth0 issues
- Verify callback URLs in Auth0 dashboard include:
  - `http://localhost:3000/api/auth/callback` (local)
  - `https://personal-finance.namelesscompany.cc/api/auth/callback` (prod)
- Verify logout URLs include both URLs

### Database issues
```bash
# Reset database (WARNING: deletes all data!)
docker compose down -v
docker compose up -d
docker compose exec api python manage.py migrate
```

---

## 📦 Deploying to Production

### First-time Setup

1. **Infrastructure:** Run Terraform in `namesless-company-infra`
2. **Database:** RDS should auto-create, run migrations manually first time
3. **Secrets:** Add all secrets to AWS Parameter Store
4. **Frontend:** Connect GitHub repo to Cloudflare Pages
5. **Backend:** Set up Jenkins pipeline

### Regular Deployments

**Frontend:**
```bash
git checkout main
git pull
git merge feature-branch
git push origin main
# Cloudflare auto-deploys in ~2 minutes
```

**Backend:**
```bash
git checkout main
git pull
git merge feature-branch
git push origin main
# Jenkins auto-deploys in ~5 minutes
```

### Rollback

**Frontend:** Use Cloudflare dashboard to rollback to previous deployment

**Backend:** 
```bash
# Revert to previous ECS task definition
aws ecs update-service --cluster nairatrack --service nairatrack-api --task-definition nairatrack-api:PREVIOUS_VERSION
```
