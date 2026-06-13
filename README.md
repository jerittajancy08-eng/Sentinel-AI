# 🛡️ Sentinel AI

### Multi-Agent Scam Investigation Network

**Microsoft Agents League Hackathon · Reasoning Agents Track**

Sentinel AI investigates suspicious emails, SMS, WhatsApp messages, job
offers, investment pitches, and phishing links — not with one model
guessing, but with **four independent specialist agents** that investigate
in parallel, plus a **Judge Agent** that weighs their evidence, resolves
disagreements, and delivers a single, explainable verdict.

> "Four agents investigate. One judge decides."

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture Diagram](#architecture-diagram)
- [Multi-Agent Workflow](#multi-agent-workflow)
- [Agent Descriptions](#agent-descriptions)
- [Microsoft Foundry Integration](#microsoft-foundry-integration)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [API Endpoints](#api-endpoints)
- [Demo Walkthrough](#demo-walkthrough)
- [Screenshots](#screenshots)
- [Future Enhancements](#future-enhancements)
- [Team](#team)

---

## Project Overview

Scam messages are everywhere — fake bank alerts, lottery wins, job offers
that ask for a "registration fee," and phishing links impersonating UPI
apps, couriers, and government agencies. Most detection tools run a single
model over the text and return a single number, with little explanation of
*why*.

Sentinel AI instead runs an **investigation**: four specialist agents
independently analyze the message from different angles — language,
structure, threat intelligence, and sender identity — and a Judge Agent
reasons over their combined findings to produce a grounded, evidence-backed
verdict with concrete recommendations.

## Problem Statement

- Scam messages constantly evolve, evading simple keyword filters.
- Single-model classifiers are black boxes — users don't know *why*
  something was flagged, which erodes trust and makes appeals impossible.
- Existing tools rarely combine **linguistic analysis**, **pattern
  matching**, **threat intelligence**, and **sender verification** into one
  coherent, explainable assessment.

## Solution

Sentinel AI's **Orchestrator Agent** receives a message and dispatches it
**in parallel** to four specialist agents, each producing an independent
risk score, evidence list, and reasoning. A **Judge Agent** then performs
multi-step reasoning over all four findings — weighing confidence,
resolving disagreements (e.g. a strong Knowledge Agent match outweighs a
weak Content Agent signal), and categorizing the scam type — before issuing
a final **Scam Risk Report**:

```json
{
  "final_score": 94,
  "verdict": "SCAM",
  "confidence": "HIGH",
  "scam_category": "Bank KYC Phishing",
  "evidence": ["...", "..."],
  "recommendations": ["...", "..."]
}
```

The entire investigation streams live to the frontend via Server-Sent
Events, so users watch each agent "light up" as it completes — making the
multi-agent reasoning process tangible, not hidden.

## Architecture Diagram

Full system flow, sequence diagram, and repository layout:
**[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)**

```
User
  │
  ▼
Investigation Gateway (FastAPI)
  │
  ▼
Orchestrator Agent ── dispatches in parallel ──┐
  │                                              │
  ├── Content Agent    (linguistic analysis)    │
  ├── Pattern Agent     (template matching)     │
  ├── Knowledge Agent    (threat intel / Foundry retrieval)
  └── Identity Agent      (sender authenticity) │
  │                                              │
  ▼ ◄────────────────────────────────────────────
Judge Agent (aggregates, resolves disagreements, verdict)
  │
  ▼
Scam Risk Report
  ├── Risk Score (0-100)
  ├── Verdict (SCAM / SUSPICIOUS / SAFE / ...)
  ├── Evidence
  └── Recommendations
```

## Multi-Agent Workflow

1. **User submits** suspicious text via the frontend (paste email/SMS/etc.)
2. **Orchestrator** dispatches the text to all four specialist agents
   *simultaneously* (`asyncio.gather` / parallel async tasks)
3. Each specialist returns a structured `AgentResult`:
   `risk_score`, `risk_level`, `evidence[]`, `reasoning`, `confidence`,
   agent-specific `metadata`
4. Results stream to the UI via **Server-Sent Events** as each agent
   finishes — the "Live Agent Reasoning" view
5. **Judge Agent** receives all four results, performs confidence-weighted
   aggregation with an agreement bonus (multiple high-risk findings raise
   confidence in a SCAM verdict), categorizes the scam type, and writes a
   multi-step reasoning narrative
6. The final **`InvestigationReport`** is returned to the frontend and
   rendered as the Scam Risk Report

## Agent Descriptions

| Agent | Role | Key Signals |
|---|---|---|
| **Content Agent** | Linguistic & psychological manipulation analysis | Urgency language, emotional manipulation, reward/threat baiting |
| **Pattern Agent** | Structural scam template matching | Known templates (lottery, advance-fee, job scams, OTP fraud), suspicious URLs, monetary patterns |
| **Knowledge Agent** | Threat intelligence retrieval (Foundry grounding) | Matches against Sentinel's threat KB — 8 documented campaign types, suspicious domain blocklist, brand-impersonation targets |
| **Identity Agent** | Sender authenticity verification | Domain spoofing, brand impersonation, unofficial communication channels |
| **Judge Agent** | Final arbiter | Confidence-weighted aggregation, disagreement resolution, scam categorization, recommendations |

Each agent's code lives in `agents/<name>_agent.py` and exposes a single
`async def run(text) -> AgentResult` (Judge: `run(text, agent_results)`),
making it trivial to add new specialists to the roster.

## Microsoft Foundry Integration

Sentinel AI is built **Foundry-first**, with a layered provider strategy so
the project runs reliably on free-tier accounts while showcasing the full
Foundry Agent Service when configured:

1. **Microsoft Foundry Agent Service** (`core/foundry_agent_service.py`) —
   each specialist is a persistent Foundry Agent with its own instructions
   and tools, run via Threads + Runs. The Knowledge Agent calls a
   `query_threat_knowledge_base` function tool (Foundry grounded
   retrieval); the Judge Agent calls `submit_agent_finding` to build an
   auditable reasoning trace. See
   **[`docs/FOUNDRY_UPGRADE.md`](docs/FOUNDRY_UPGRADE.md)** for the full
   migration plan.
2. **Azure OpenAI** (`AZURE_OPENAI_*`) — direct chat-completions fallback
   if Foundry Agent Service isn't configured.
3. **OpenAI** (`OPENAI_API_KEY`) — free-tier / student-account fallback.
4. **Mock mode** (`SENTINEL_MOCK_MODE=true`) — deterministic heuristic
   scoring with no API key, so the full demo always works offline.

`core/foundry_client.py` selects the highest-available tier automatically
and degrades gracefully on any failure — **no agent code changes** when
moving between tiers.

## Tech Stack

**Frontend**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS
- Server-Sent Events for live agent reasoning

**Backend**
- Python 3.12 + FastAPI
- `asyncio` parallel agent orchestration
- Server-Sent Events streaming

**AI**
- Microsoft Foundry Agent Service (`azure-ai-projects`, `azure-ai-agents`)
- Azure OpenAI
- Sentinel Threat Intelligence KB (`data/scam_kb.json`) — designed as a
  drop-in target for Azure AI Search / vector search

**Deployment**
- Docker + Docker Compose
- Azure App Service (backend, container or code deploy)
- Azure Static Web Apps (frontend)

## Installation

### Prerequisites
- Python 3.12+
- Node.js 20+
- (Optional) Docker & Docker Compose
- (Optional) Azure CLI for deployment

### Clone & install

```bash
git clone https://github.com/<your-org>/sentinel-ai.git
cd sentinel-ai

# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Configure environment

```bash
cp .env.example .env
# Edit .env — defaults to SENTINEL_MOCK_MODE=true, which requires no API keys
```

## Running Locally

### Option A — Manual (two terminals)

```bash
# Terminal 1 — backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Visit **http://localhost:3000**. The backend runs at
**http://localhost:8000** (interactive docs at `/docs`).

### Option B — Docker Compose

```bash
docker compose up --build
```

Same URLs as above. Set real provider keys in your shell environment before
running to use live Foundry/Azure OpenAI instead of mock mode.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check + active provider info |
| `GET` | `/api/agents` | Lists all agents and their roles |
| `GET` | `/api/kb/stats` | Threat knowledge base statistics |
| `POST` | `/api/investigate` | Run a full investigation, return the complete report |
| `POST` | `/api/investigate/stream` | Run an investigation, streaming live agent results via SSE |

**Example request:**

```bash
curl -X POST http://localhost:8000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"text": "Congratulations! You won ₹50,000. Click here immediately to claim your reward.", "content_type": "sms"}'
```

## Demo Walkthrough

See **[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)** for the full 3-minute
presentation script. Quick version:

1. Open the landing page — the agent network diagram is visible and idle
2. Paste a sample scam message (or click one of the provided samples)
3. Click **Run Investigation** — watch all four agent nodes light up and
   report scores in real time
4. The Judge Agent node activates, then the **Scam Risk Report** renders:
   risk gauge, verdict, evidence, recommendations, and a per-agent
   breakdown
5. Try a legitimate message to show the contrast — low score, "SAFE"
   verdict, minimal evidence

## Screenshots

> Add screenshots/GIFs of the landing page, live agent network animation,
> and final Scam Risk Report here before submission.

| Landing & Agent Network | Live Investigation | Scam Risk Report |
|---|---|---|
| `docs/screenshots/landing.png` | `docs/screenshots/live.png` | `docs/screenshots/report.png` |

## Future Enhancements

See **[`docs/WINNING_IMPROVEMENTS.md`](docs/WINNING_IMPROVEMENTS.md)** for a
ranked list of follow-up features (Azure AI Search-backed Knowledge Agent,
Admin/Analytics dashboard, multi-language support, browser extension,
WhatsApp bot integration, and more).

## Team

| Name | Role |
|---|---|
| _Add your name_ | Lead Engineer / Architecture |
| _Add teammate_ | Frontend / UX |
| _Add teammate_ | AI / Agent Design |

---

**Built for the Microsoft Agents League Hackathon — Reasoning Agents
Track.** Powered by Microsoft Foundry.
