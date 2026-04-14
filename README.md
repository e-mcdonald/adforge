# AdForge — Agentic Ad Creative System

An agentic AI pipeline that takes a product, avatar, and ad angle as input and outputs a full direct response ad package using Breakthrough Advertising principles.

---

## Quick Start

### 1. Backend

```bash
cd adforge/backend
cp .env.example .env
# Edit .env with your API keys

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000
API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health

### 2. Frontend

```bash
cd adforge/frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

### 3. Verify

```bash
# Health check
curl http://localhost:8000/health

# Model status (shows Ollama availability)
curl http://localhost:8000/api/models/status
```

---

## Model Setup

AdForge uses different models per task to balance cost and quality.

| Task              | Model              | Provider  |
|-------------------|--------------------|-----------|
| Research extract  | llama3.1:8b        | Ollama    |
| Research synthesis| claude-sonnet-4-5  | Anthropic |
| Strategy          | claude-sonnet-4-5  | Anthropic |
| Copy              | claude-opus-4-5    | Anthropic |
| Creative Brief    | llama3.1:8b        | Ollama    |
| QA                | llama3.1:8b        | Ollama    |

### Local Models (Ollama) — free, runs on your machine

Required: 16GB+ unified memory (Mac) or 8GB+ VRAM (GPU)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model used by AdForge
ollama pull llama3.1:8b

# Verify it's running
ollama list
```

If Ollama is unavailable, AdForge automatically falls back to gpt-4o-mini for non-copy tasks. The system will never crash due to model availability.

### API Keys (add to backend/.env)

```
ANTHROPIC_API_KEY=   ← required (Copy Agent uses Claude Opus)
OPENAI_API_KEY=      ← required (DALL-E image gen + fallback)
```

### Cost Per Campaign (approximate)

| Configuration                          | Estimated Cost   |
|----------------------------------------|-----------------|
| Local models ON + Claude Opus copy     | ~$0.25–0.40     |
| Local models ON + Claude Sonnet copy   | ~$0.10–0.20     |
| Local models OFF + Claude Opus copy    | ~$1.20–1.80     |
| Local models OFF + Claude Sonnet copy  | ~$0.60–1.00     |

---

## Pipeline Stages

```
Avatar Builder → Campaign Builder → Launch Pipeline
                                        ↓
                               [1] Research Agent
                                 - Scrapes product URL
                                 - Pulls Reddit VoC
                                 - Synthesizes with Claude Sonnet
                                        ↓
                               [2] Strategy Agent (Sonnet)
                                 - Generates 3 distinct angles
                                        ↓
                               [3] Copy Agent (Opus)
                                 - Full copy package per angle
                                 - Headlines, body, CTAs, TikTok frames
                                        ↓
                               [4] Creative Brief Agent (llama3.1:8b)
                                 - Visual direction + DALL-E prompts
                                        ↓
                               [5] Image Gen Agent (DALL-E 3)
                                 - 3 formats per angle (Feed, Story, TikTok)
                                        ↓
                               [6] QA Agent (llama3.1:8b)
                                 - Scores hook, awareness match, specificity
                                 - Flags banned patterns + Meta policy issues
```

---

## Docker

### Local with Docker Compose

```bash
# Requires .env to exist at backend/.env with API keys
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000

# Health check through nginx proxy
curl http://localhost:3000/api/health
```

**Note on Ollama in Docker:** Ollama must run on the HOST machine. The backend container connects to it via `host.docker.internal:11434` (Mac/Windows) or `172.17.0.1:11434` (Linux).

---

## AWS Deploy (Phase 7)

### Prerequisites

- AWS CLI configured
- Terraform >= 1.5 installed
- Docker installed

### Deploy

```bash
# Set ECR registry URL (from AWS Console → ECR)
export ECR_REGISTRY=<your-account-id>.dkr.ecr.us-east-1.amazonaws.com
export AWS_REGION=us-east-1

./deploy.sh
```

### Terraform only (plan first)

```bash
cd terraform
terraform init

# Review plan before applying
terraform plan \
  -var="openai_api_key=YOUR_KEY" \
  -var="anthropic_api_key=YOUR_KEY"

# Apply when ready
terraform apply \
  -var="openai_api_key=YOUR_KEY" \
  -var="anthropic_api_key=YOUR_KEY"
```

**Note:** `terraform apply` provisions real AWS resources and will incur costs (~$15–30/month for t3.small + S3 + ECR).

---

## Project Structure

```
adforge/
├── backend/
│   ├── main.py                 # FastAPI app + startup
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # Avatar + Campaign ORM models
│   ├── config/
│   │   ├── models.py           # MODEL_CONFIG routing table
│   │   └── model_router.py     # get_llm() + Ollama check + cost estimate
│   ├── agents/
│   │   ├── orchestrator.py     # LangGraph StateGraph pipeline
│   │   ├── research_agent.py   # Scrape + Reddit VoC + Sonnet synthesis
│   │   ├── strategy_agent.py   # 3-angle strategy (Sonnet)
│   │   ├── copy_agent.py       # Full copy packages (Opus)
│   │   ├── creative_brief_agent.py  # Visual direction + DALL-E prompts
│   │   ├── image_gen_agent.py  # DALL-E 3 image generation
│   │   └── qa_agent.py         # Copy audit + Meta compliance
│   ├── routers/
│   │   ├── avatars.py
│   │   ├── campaigns.py
│   │   └── models_router.py
│   ├── schemas/
│   │   ├── avatar.py
│   │   └── campaign.py
│   ├── static/campaigns/       # Generated images stored here
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Layout + routing + model status sidebar
│   │   ├── pages/
│   │   │   ├── AvatarBuilder.jsx
│   │   │   ├── CampaignBuilder.jsx
│   │   │   └── CampaignOutput.jsx
│   │   └── components/
│   │       └── AvatarCard.jsx
│   ├── nginx.conf
│   └── Dockerfile
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── ec2.tf
│   ├── s3.tf
│   ├── ecr.tf
│   ├── security_groups.tf
│   ├── iam.tf
│   ├── ssm.tf
│   └── userdata.sh.tpl
├── docker-compose.yml
├── deploy.sh
└── README.md
```

---

## Environment Variables

See `backend/.env.example` for full reference.

| Variable           | Required | Purpose                                  |
|--------------------|----------|------------------------------------------|
| ANTHROPIC_API_KEY  | Yes      | Strategy, research synthesis, copy agents|
| OPENAI_API_KEY     | Yes      | DALL-E 3 image gen + gpt-4o-mini fallback|
| OLLAMA_BASE_URL    | No       | Default: http://localhost:11434          |
| ENV                | No       | development (default) or production      |
| S3_BUCKET          | Prod only| S3 bucket name for image storage         |
| AWS_REGION         | Prod only| Default: us-east-1                       |
