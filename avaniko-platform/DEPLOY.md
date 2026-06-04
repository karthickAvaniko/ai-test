# Avaniko AI Platform — Deployment Guide

## Architecture

```
Internet
  │
  ▼
Nginx (port 80/443)   ← SSL termination
  │
  ▼
FastAPI Backend        ← API gateway (hides RunPod)
  │           │
  ▼           ▼
PostgreSQL   Redis     ← Data + Rate limiting
              │
              ▼ (private, never exposed)
         RunPod Server
         └── Qwen3.6 MoE
```

---

## Step 1 — Server Requirements

Any Linux VPS with Docker:
- OS: Ubuntu 22.04 LTS
- RAM: 2GB minimum (4GB recommended)
- CPU: 2 cores
- Storage: 20GB
- Providers: Hetzner (€4/mo), DigitalOcean ($6/mo), Vultr ($6/mo)

---

## Step 2 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

---

## Step 3 — Clone and Configure

```bash
# Upload your project to server
scp -r avaniko-platform/ user@your-server:/opt/avaniko/

# SSH into server
ssh user@your-server
cd /opt/avaniko

# Copy and fill env file
cp .env.example .env
nano .env
```

Fill these in .env:
```
SECRET_KEY=<run: openssl rand -hex 32>
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
RUNPOD_GATEWAY_URL=http://your-runpod-ip:2222
RUNPOD_API_KEY=sk-ava-your-internal-key
```

---

## Step 4 — SSL Certificate

```bash
# Install certbot
sudo apt install certbot -y

# Get certificate (point domain to this server IP first)
sudo certbot certonly --standalone -d api.avaniko.com

# Copy to nginx ssl folder
sudo mkdir -p /opt/avaniko/nginx/ssl
sudo cp /etc/letsencrypt/live/api.avaniko.com/fullchain.pem /opt/avaniko/nginx/ssl/
sudo cp /etc/letsencrypt/live/api.avaniko.com/privkey.pem   /opt/avaniko/nginx/ssl/
```

---

## Step 5 — Deploy

```bash
cd /opt/avaniko
docker compose up -d --build

# Check all services running
docker compose ps

# View logs
docker compose logs -f backend
```

---

## Step 6 — Build Frontend

```bash
cd frontend
npm install
VITE_API_URL=https://api.avaniko.com npm run build

# Deploy dist/ to:
# - Vercel: vercel --prod
# - Netlify: netlify deploy --prod --dir=dist
# - Or serve via nginx from /opt/avaniko/frontend/dist
```

---

## Step 7 — IIS Deployment (Windows)

If deploying backend on Windows IIS:

```
1. Install Python 3.12 on Windows server
2. Install pip requirements
3. Install IIS + URL Rewrite + Application Request Routing
4. Configure IIS as reverse proxy → http://localhost:8000
5. Run uvicorn as Windows Service:
   pip install pywin32
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Or use **Docker Desktop on Windows** and keep docker-compose.yml as-is.

---

## API Endpoints Summary

| Method | URL                         | Auth      | Description           |
|--------|-----------------------------|-----------|-----------------------|
| POST   | /auth/signup                | None      | Create account        |
| POST   | /auth/login                 | None      | Get JWT token         |
| GET    | /auth/me                    | JWT       | Current user          |
| POST   | /v1/api-keys/create         | JWT       | Create API key        |
| GET    | /v1/api-keys                | JWT       | List API keys         |
| DELETE | /v1/api-keys/{id}           | JWT       | Revoke key            |
| POST   | /v1/chat/completions        | x-api-key | Chat (OpenAI compat)  |
| GET    | /v1/models                  | x-api-key | List models           |
| POST   | /v1/embeddings              | x-api-key | Get embeddings        |
| GET    | /v1/usage                   | x-api-key | Usage stats           |
| POST   | /v1/projects                | x-api-key | Create project        |
| GET    | /v1/projects                | x-api-key | List projects         |
| GET    | /admin/stats                | JWT+admin | Global stats          |

---

## SDK Usage

```bash
pip install avaniko-ai
```

```python
from avaniko_ai import Avaniko

client = Avaniko(api_key="ava-sk-xxxx")

# Simple chat
print(client.chat("Hello!"))

# With project (stored system prompt)
print(client.chat("Extract invoice", project_id="proj-xxx"))

# Streaming
for token in client.stream("Write a poem"):
    print(token, end="", flush=True)

# Embeddings
vector = client.embed("Some text")

# List models
models = client.models()
```
