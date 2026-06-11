# TZ Tourism Radar SaaS

**Geopolitical Intelligence for Tanzanian Tourism — Real-time market monitoring across China & Russia.**

This SaaS platform continuously scans Chinese and Russian social media, news, and forums for signals relevant to Tanzanian tourism. It collects raw posts via Exa AI search, translates and summarizes them (with optional OpenAI integration), detects crisis signals, and presents actionable insights in a Next.js dashboard.

---

## Table of Contents

- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Keyword Matrix](#keyword-matrix)
- [Configuration](#configuration)
- [License](#license)

---

## Architecture

```
┌─────────────┐     POST /api/v1/radar/trigger     ┌──────────────┐
│   Next.js   │ ──────────────────────────────────▶ │  FastAPI     │
│  Dashboard  │                                     │  Backend     │
│  :3000      │ ◀────────────────────────────────── │  :8000       │
└─────────────┘     GET /api/v1/radar/{job_id}      └──────┬───────┘
                                                            │
                                                  background task
                                                            │
                                                    ┌───────▼───────┐
                                                    │   Scanner     │
                                                    │               │
                                                    │  ┌─────────┐  │
                                                    │  │ mcporter│  │
                                                    │  │  + Exa  │  │
                                                    │  └─────────┘  │
                                                    │               │
                                                    │  heuristic or │
                                                    │  OpenAI       │
                                                    └───────────────┘
```

- **Backend** — FastAPI (Python) with async background tasks via `BackgroundTasks`
- **Scanner** — `mcporter` CLI wraps the Exa MCP server for real-time web search across Chinese and Russian language content
- **Analysis** — Heuristic pattern matching (zero API cost) or optional OpenAI GPT-4o-mini for AI-powered translation and summarization
- **Frontend** — Next.js 14 dashboard with real-time polling, sentiment gauges, and crisis alerts

---

## How It Works

### 1. Trigger a Scan

The user clicks **"Run Scan"** on the dashboard. The frontend sends a POST request to `/api/v1/radar/trigger` with a `client_id` and optional custom keywords.

### 2. Background Processing

The backend spawns an async background task that runs two scans in parallel:

- **China market scan** — ~24 keywords across 4 categories
- **Russia market scan** — ~19 keywords across 4 categories

Each keyword is searched via `mcporter call exa.web_search_exa(...)`, which queries Exa's AI-powered semantic search engine. The per-keyword timeout is 45 seconds; slow keywords are skipped individually without hanging the whole scan.

### 3. Parse and Analyze

Raw search results are parsed into structured posts. The system then:

1. Checks for crisis signals using pattern matching (e.g. scams, safety issues, health risks)
2. Categorizes posts into insights (payment friction, visa queries, flight discussions, investment sentiment)
3. If `OPENAI_API_KEY` is set, passes all posts to GPT-4o-mini for translation and structured summarization
4. If no API key is set, falls back to deterministic heuristic analysis

### 4. Poll for Results

The frontend polls `GET /api/v1/radar/{job_id}` every 3 seconds until the status is `"COMPLETED"`. The report contains:

- Executive summary
- China market insights (trends, sentiment, actions)
- Russia market insights
- Crisis alerts
- Raw post count

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Scanner** | mcporter CLI + Exa MCP server |
| **AI** | OpenAI GPT-4o-mini (optional) or heuristic analysis |
| **Frontend** | Next.js 14, React 18, Tailwind CSS, Axios |
| **Search** | Exa AI (free tier, no API key required) |
| **Deployment** | Docker-ready (see docker-compose) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### 1. Clone the Repository

```bash
git clone https://github.com/mashimi/Tanzania-Russiav1.git
cd Tanzania-Russiav1
```

### 2. Backend Setup

**Important:** The backend code is inside `tz-radar-saas/backend/`, NOT at a top-level `backend/` folder. All commands below assume you are starting from the repository root (`Tanzania-Russiav1/`).

```powershell
# Step 1 — Navigate to the backend folder
cd tz-radar-saas\backend

# Step 2 — Create a virtual environment inside the backend folder
python -m venv .venv

# Step 3 — Activate the virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Windows CMD:
# .venv\Scripts\activate

# After activation you should see "(.venv)" in your terminal prompt.
# Step 4 — Install backend dependencies into this environment
pip install -r requirements.txt
```

Create a `.env` file inside `tz-radar-saas/backend/`:

```env
# Optional: Enables AI-powered translation & summarization
OPENAI_API_KEY=sk-your-openai-key
```

> **Troubleshooting:** If you get `No module named uvicorn`, your venv is not activated or you installed packages in the wrong environment. Make sure `(.venv)` appears in your prompt before running `pip install -r requirements.txt`.

### 3. Frontend Setup

```bash
# From the repo root, navigate to frontend
cd tz-radar-saas/frontend

npm install
```

Create a `.env.local` file inside `tz-radar-saas/frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start Both Services

Make sure your virtual environment is activated before starting the backend.

**Backend** (from `tz-radar-saas/backend/`):
```bash
# Ensure venv is active, then:
python -m uvicorn main:app --reload --port 8000
```

**Frontend** (from `tz-radar-saas/frontend/`):
```bash
npm run dev
```

Visit `http://localhost:3000/dashboard` to see the dashboard.

> **Note about the scanner:** The scanner requires `mcporter` to be installed globally. Run `npm install -g mcporter` and configure Exa: `mcporter config add exa https://mcp.exa.ai/mcp`

> **Important:** The backend path is `tz-radar-saas/backend`, not `backend`. Running `cd backend` from the repo root will fail because the directory is nested inside `tz-radar-saas/`.

---

## API Reference

### Health Check

```http
GET /health
```

Response:
```json
{"status": "ok", "service": "tz-radar-api", "version": "2.0.0"}
```

### Trigger a Scan

```http
POST /api/v1/radar/trigger
Content-Type: application/json

{
  "client_id": "client-123",
  "custom_keywords": ["Zanzibar luxury resorts"]
}
```

Response:
```json
{"job_id": "uuid-string", "status": "processing"}
```

### Get Report (Poll)

```http
GET /api/v1/radar/{job_id}
```

Response (when complete):
```json
{
  "id": "uuid-string",
  "clientId": "client-123",
  "status": "COMPLETED",
  "executiveSummary": "...",
  "chinaInsights": [...],
  "russiaInsights": [...],
  "crisisAlerts": [...],
  "reportDate": "2026-06-11T09:52:58+00:00",
  "raw_post_count": 72
}
```

### List Reports

```http
GET /api/v1/radar?client_id=client-123
```

Response:
```json
{
  "reports": [...],
  "total": 5
}
```

---

## Keyword Matrix

The scanner uses categorized keyword matrices to cover the full spectrum of market signals.

### Chinese Market (`KEYWORD_MATRIX_CN`) — 24 keywords

| Category | Keywords |
|----------|----------|
| **Tourism** (7) | Travel guides, Zanzibar hotel recommendations, safari tips, Serengeti Great Migration, Kilimanjaro climbing, Chinese-speaking guides, tourism safety |
| **Investment** (10) | Investment opportunities, China-Tanzania cooperation, President economy, Zanzibar business inspection, Belt & Road, mining cooperation, agriculture investment, economic cooperation, real estate investment, Dar es Salaam port |
| **Logistics** (4) | Visa policy, direct flights, flight prices, TAZARA railway |
| **Luxury** (3) | Zanzibar luxury resorts, high-end custom tours, Serengeti luxury tents |

### Russian Market (`KEYWORD_MATRIX_RU`) — 19 keywords

| Category | Keywords |
|----------|----------|
| **Tourism** (5) | Zanzibar vacation 2026, safari reviews, all-inclusive tourism, Russian tourists in Tanzania, visa news |
| **Investment** (8) | Investments 2026, President Samia Suluhu Hassan, Zanzibar business delegation, Russia-Tanzania economy, tourism partnership, Zanzibar investments, Dar es Salaam business mission, gold mining |
| **Logistics** (3) | Direct flights, flight from Moscow, card payment |
| **Luxury** (3) | Luxury hotels Zanzibar, VIP tours, Serengeti luxury safari |

---

## Configuration

### Environment Variables (Backend)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | No | Enables AI translation & summarization via GPT-4o-mini |
| Any dotenv vars | No | Loaded from `backend/.env` via `python-dotenv` |

### Environment Variables (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API base URL |

### VS Code Settings

A `.vscode/settings.json` is provided for Pylance:

```json
{
  "python.defaultInterpreterPath": "C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
  "python.analysis.extraPaths": ["tz-radar-saas/backend"]
}
```

Adjust the interpreter path to match your local Python installation.

---

## License

MIT