# Step-by-Step: Build, Host & Deploy the AI Lead Scoring API

---

## What You're Building

A production-grade FastAPI microservice that:
- Scores leads with a trained ML model (Random Forest)
- Authenticates requests via API key
- Rate limits to 30 requests/minute per IP
- Logs every prediction asynchronously
- Exposes /metrics for monitoring
- Deploys to Render in minutes
- Can be containerized with Docker later

---

## Your Folder Structure

```
lead_scoring_api/
├── main.py              ← FastAPI app (the API server)
├── train_model.py       ← ML training script (run once)
├── requirements.txt     ← Python dependencies
├── build.sh             ← Render build script
├── Dockerfile           ← Docker container definition
├── docker-compose.yml   ← Local Docker dev setup
├── .env.example         ← Environment variable template
├── .gitignore           ← Files to exclude from Git
└── README.md
```

---

## PHASE 1 — Local Setup

### Step 1: Create the project folder

```bash
mkdir lead_scoring_api
cd lead_scoring_api
```

### Step 2: Create a virtual environment

```bash
python -m venv venv

# Activate it:
# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal — this isolates your project's packages.

### Step 3: Copy all the project files into this folder

Paste in: main.py, train_model.py, requirements.txt, build.sh, Dockerfile,
docker-compose.yml, .env.example, .gitignore

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, scikit-learn, slowapi, pydantic[email], etc.

### Step 5: Train the model

```bash
python train_model.py
```

Expected output:
```
✅ Model trained and saved as lead_model.pkl
   Training samples : 500
   Features         : ['job_seniority', 'company_size', ...]
   Classes          : cold(0), warm(1), hot(2)
```

This creates `lead_model.pkl` in your project folder. This is the saved brain of your API.

### Step 6: Run the API locally

```bash
uvicorn main:app --reload --port 8000
```

`--reload` means the server restarts automatically when you edit main.py. Remove it in production.

Visit: http://localhost:8000
You should see:
```json
{
  "service": "AI Lead Scoring API",
  "version": "1.0.0",
  "status": "live"
}
```

### Step 7: Test the API locally

Open your browser and go to:
http://localhost:8000/docs

This is the automatic Swagger UI — FastAPI generates it from your code for free.
You can test every endpoint here without Postman.

Test with curl:

```bash
curl -X POST http://localhost:8000/score-lead \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@techcorp.io",
    "company": "TechCorp",
    "job_title": "VP of Operations",
    "industry": "SaaS",
    "company_size": 3,
    "budget_flag": 1,
    "timeline": 2,
    "pain_points": 4,
    "message": "We need to automate our entire pipeline immediately."
  }'
```

Expected response:
```json
{
  "request_id": "a3f9c2d1",
  "timestamp": "2025-01-01T12:00:00Z",
  "name": "Jane Doe",
  "tier": "hot",
  "score": 89,
  "routing_action": "immediate_outreach",
  "confidence": 0.98,
  "model_version": "1.0.0",
  ...
}
```

---

## PHASE 2 — Push to GitHub

Render deploys directly from your GitHub repo.

### Step 1: Initialize Git

```bash
git init
git add .
git commit -m "feat: initial AI lead scoring API"
```

### Step 2: Create a GitHub repo

1. Go to https://github.com → New Repository
2. Name it: `lead-scoring-api`
3. Keep it Public (for portfolio visibility)
4. Do NOT initialize with README (you already have one)

### Step 3: Push your code

```bash
git remote add origin https://github.com/YOUR-USERNAME/lead-scoring-api.git
git branch -M main
git push -u origin main
```

Important: `lead_model.pkl` is in `.gitignore` — the model will be trained
fresh on Render during each deployment. This is correct behavior.

---

## PHASE 3 — Deploy to Render (Free Tier)

### Step 1: Create a Render account

Go to https://render.com → Sign up with GitHub

### Step 2: New Web Service

1. Dashboard → New → Web Service
2. Connect your GitHub account
3. Select your `lead-scoring-api` repository
4. Click Connect

### Step 3: Configure the service

Fill in these fields exactly:

| Setting        | Value                                              |
|----------------|----------------------------------------------------|
| Name           | lead-scoring-api                                   |
| Runtime        | Python 3                                           |
| Build Command  | `bash build.sh`                                    |
| Start Command  | `uvicorn main:app --host 0.0.0.0 --port $PORT`     |
| Instance Type  | Free                                               |

### Step 4: Add environment variables

In the Render dashboard → Environment → Add the following:

| Key      | Value                           |
|----------|---------------------------------|
| API_KEYS | your-secret-key-here            |

Choose a strong key. You'll use this in n8n as the X-API-Key header.

### Step 5: Deploy

Click "Create Web Service". Render will:
1. Clone your repo
2. Run `bash build.sh` (installs deps + trains model)
3. Start the API with uvicorn

Watch the logs tab — deployment takes ~3-5 minutes on the free tier.

### Step 6: Verify your live API

Once deployed, Render gives you a URL like:
`https://lead-scoring-api.onrender.com`

Test it:
```bash
curl https://lead-scoring-api.onrender.com/health
```

Expected:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": "1.0.0"
}
```

Note: Free tier Render services spin down after 15 minutes of inactivity.
First request after sleep takes ~30 seconds (cold start). This is normal
for free tier — upgrade to paid ($7/mo) for always-on.

---

## PHASE 4 — Docker (When You're Ready to Level Up)

You don't need Docker for Render — but when you move to AWS, GCP, or DigitalOcean,
Docker makes your app fully portable.

### How the Dockerfile works

The Dockerfile uses a multi-stage build:

Stage 1 (builder): Full Python environment → installs deps → trains model
Stage 2 (runtime): Lean Python environment → copies only what's needed

This makes the final image smaller (~200MB vs ~700MB) and more secure.

### Run locally with Docker

```bash
# Build the image
docker build -t lead-scoring-api .

# Run it
docker run -p 8000:8000 -e API_KEYS=dev-key-12345 lead-scoring-api
```

Visit: http://localhost:8000

### Run with Docker Compose (easier for local dev)

```bash
docker-compose up --build
```

To stop:
```bash
docker-compose down
```

### Deploy Docker to Render (when upgrading)

Render also supports Dockerfile deployments:
1. Dashboard → New → Web Service
2. Select your repo
3. Change Runtime to: Docker
4. Render auto-detects your Dockerfile and builds it

---

## What Makes This Senior-Level

Here's what separates this from a beginner FastAPI tutorial:

1. API Key Authentication — every endpoint protected via X-API-Key header
2. Rate Limiting — slowapi blocks abusive callers at 30 req/min
3. Model Registry pattern — the model is a stateful singleton with metadata
4. Lifespan context manager — proper startup/shutdown lifecycle (FastAPI best practice)
5. Background Tasks — prediction logging is async so it never slows the response
6. Custom Pydantic validators — email normalization, seniority extraction, industry validation
7. /metrics endpoint — exposes prediction counts and tier distribution
8. Request timing middleware — every response includes X-Process-Time-Ms header
9. Multi-stage Dockerfile — lean, secure, production-ready container
10. Named feature predictions — no sklearn warnings, proper DataFrame-based inference
11. Structured logging — timestamped, leveled logs with request IDs
12. UUID request IDs — every prediction is traceable end-to-end

---

## Troubleshooting

| Problem                     | Fix                                                        |
|-----------------------------|------------------------------------------------------------|
| `lead_model.pkl` not found  | Run `python train_model.py` first                         |
| 401 Unauthorized            | Add `X-API-Key: dev-key-12345` header to your request     |
| 429 Too Many Requests       | You hit the rate limit — wait 60 seconds                  |
| Cold start on Render        | Normal on free tier — first request after sleep is slow   |
| Port already in use         | Run `uvicorn main:app --port 8001` to use a different port |
