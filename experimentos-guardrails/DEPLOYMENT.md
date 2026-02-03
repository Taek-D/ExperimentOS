# Deployment Guide

## Frontend (Vercel)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy from frontend directory:
```bash
cd experimentos-guardrails
vercel
```

3. Set environment variable in Vercel dashboard:
- `VITE_API_URL`: Your FastAPI backend URL (e.g., `https://your-backend.fly.io/api`)

## Backend Deployment Options

### Option 1: Fly.io (Recommended for FastAPI)

1. Install Fly CLI:
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

2. Create `fly.toml` in project root:
```toml
app = "experimentos-api"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

3. Deploy:
```bash
fly auth login
fly launch
fly deploy
```

### Option 2: Railway

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Deploy:
```bash
railway login
railway init
railway up
```

## Local Development

### Backend
```bash
cd e:\프로젝트\안티그래비티 프로젝트\에이블리
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd experimentos-guardrails
npm run dev
```

## Environment Variables

### Frontend (.env.local)
```
VITE_API_URL=http://localhost:8000/api  # Development
# VITE_API_URL=https://your-backend.fly.io/api  # Production
```

### Backend
No environment variables required for basic setup.
