# KairosAI — Multi-Agent Product Launch War Room

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20Llama%203.3-orange?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-112%20passed-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

**AI-powered cross-functional war room that analyses a product launch in real time and delivers a structured Proceed / Pause / Roll Back decision.**

[Overview](#overview) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Usage](#usage) · [API](#api-reference) · [Tests](#tests) · [Project Structure](#project-structure)

</div>

---

## Overview

KairosAI simulates the kind of emergency cross-functional meeting ("war room") that product teams convene when a launch starts degrading. Five specialised AI agents — each with a distinct role and toolset — analyse a live metrics dashboard, debate the findings, and produce a structured decision backed by evidence.

**Built for:** PurpleMerit's SmartDash 2.0 feature launch assessment.

### What it does

1. Ingests a 10-day KPI time series, 35 user feedback entries, and a release notes document
2. Runs 5 AI agents in sequence — each calls real Python tool functions to analyse the data
3. Conducts a structured debate round where the Risk agent challenges assumptions
4. A Debate Moderator resolves disagreements and produces a weighted confidence score
5. Outputs a structured JSON + Markdown report with decision, risk register, action plan, and comms plan
6. Streams every step live to a React dashboard over WebSocket

### Decision output

```
FINAL DECISION : 🔴 ROLL BACK
Confidence     : 87/100 — High confidence
Tally          : ROLL_BACK: 3  |  PAUSE: 2  |  PROCEED: 0
```

---

## Architecture

### Agent pipeline

```
Mock Dashboard (metrics + feedback + release notes)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                      Orchestrator                        │
│                                                          │
│  Phase 1   ┌─────────────────┐                          │
│            │  Data Analyst   │ ← aggregate_metrics       │
│            │                 │   detect_anomalies        │
│            └────────┬────────┘   trend_compare           │
│                     │                                    │
│  Phase 2   ┌────────▼────────┐                          │
│            │ Product Manager │ ← aggregate_metrics       │
│            │ Marketing/Comms │ ← sentiment_analyzer      │
│            │ SRE/Engineering │ ← detect_anomalies        │
│            └────────┬────────┘                          │
│                     │                                    │
│  Phase 3   ┌────────▼────────┐                          │
│            │  Risk / Critic  │ ← risk_scorer             │
│            │                 │   detect_anomalies        │
│            └────────┬────────┘                          │
│                     │                                    │
│  Phase 4   ┌────────▼────────┐                          │
│            │ Debate Moderator│ reads all agent reports   │
│            └────────┬────────┘                          │
│                     │                                    │
│  Phase 5   ┌────────▼────────┐                          │
│            │  Final Decision │ weighted confidence score │
│            └─────────────────┘                          │
│                                                          │
│  Monitor   ┌─────────────────┐                          │
│  (always)  │ War Room Monitor│ live Q&A on session       │
│            └─────────────────┘                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   JSON + Markdown Report  /  React Dashboard
```

### Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq API — `llama-3.3-70b-versatile` (free) |
| Backend | Python 3.12 · FastAPI · WebSockets |
| Agents | Custom orchestration (no LangChain) |
| Tools | Pure Python functions |
| Frontend | React 18 · Vite · Tailwind CSS · Recharts |
| Tests | pytest · 112 tests · mocked LLM |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- A free Groq API key — [console.groq.com](https://console.groq.com)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/KairosAI.git
cd KairosAI

# Set your Groq API key
cp .env.example .env
# Edit .env and add:  GROQ_API_KEY=gsk_...
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

### 4. Run

Open two terminal tabs:

```bash
# Terminal 1 — API server
cd backend
uvicorn api.app:app --reload --port 8000

# Terminal 2 — React frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** and click **Start War Room**.

---

## Usage

### CLI — run the war room directly

```bash
cd backend

# Validate all imports and tools (no API call)
python main.py --dry-run

# Run the full war room
python main.py

# Run and ask the monitor a question at the end
python main.py --monitor "What did the Risk agent say about crash rate?"

# Output final JSON to stdout
python main.py --json-only

# Start the API server
python main.py --serve
```

### Web UI

| Page | URL | Description |
|---|---|---|
| War Room | `http://localhost:5173/` | Live agent streaming + decision |
| Dashboard | `http://localhost:5173/dashboard` | KPI charts + feedback analysis |
| Reports | `http://localhost:5173/reports` | Browse + download past sessions |

### Output files

Every run writes two files to `backend/reports/`:

```
reports/
├── warroom_{session_id}_{timestamp}.json   ← structured decision
└── warroom_{session_id}_{timestamp}.md     ← human-readable report
```

---

## Agents

| Agent | Role | Tools used |
|---|---|---|
| **Data Analyst** | Objective metrics, anomaly detection, trend confidence | `aggregate_metrics` · `detect_anomalies` · `trend_compare` |
| **Product Manager** | Success criteria evaluation, user impact framing | `aggregate_metrics` · `trend_compare` |
| **Marketing / Comms** | Sentiment analysis, reputation risk, comms plan | `sentiment_analyzer` |
| **Risk / Critic** | Challenges assumptions, builds risk register | `risk_scorer` · `detect_anomalies` |
| **SRE / Engineering** | SLO status, infra signals, root cause hypothesis | `aggregate_metrics` · `detect_anomalies` |
| **War Room Monitor** | Session-wide memory, live Q&A | Session memory |
| **Debate Moderator** | Resolves agent disagreements, weighted verdict | All agent reports |

### Confidence scoring

Each agent's verdict is weighted by role relevance:

| Agent | Weight |
|---|---|
| Data Analyst | 25% |
| SRE / Engineering | 22% |
| Risk / Critic | 20% |
| Product Manager | 18% |
| Marketing / Comms | 10% |
| Debate Moderator | 5% |

Agreement bonus (+8 pts) when all agents align. Split penalty (-10 pts) when no majority.

---

## Tools

Five pure Python functions called programmatically by agents:

| Tool | What it returns |
|---|---|
| `aggregate_metrics()` | Per-KPI stats: avg, baseline, current, trend, status (OK/WARN/CRITICAL) |
| `detect_anomalies()` | Z-score anomaly list, severity counts, anomaly start date |
| `sentiment_analyzer()` | Sentiment score (-1 to +1), distribution, critical signals, churn indicators |
| `trend_compare()` | Baseline vs post-launch delta per KPI, launch impact verdict |
| `risk_scorer()` | Scored risk register with likelihood, impact, mitigation, recommended posture |

---

## Structured Output

Every war room session produces a JSON document conforming to this schema:

```json
{
  "meta": {
    "session_id": "b5cd075e",
    "product": "PurpleMerit — SmartDash 2.0",
    "generated_at": "2025-07-14T10:30:00Z",
    "agents_run": ["Data Analyst", "Product Manager", "..."]
  },
  "decision": "ROLL_BACK",
  "rationale": {
    "primary_drivers": ["[Data Analyst] Crash rate 3x baseline..."],
    "metric_references": ["crash_rate: 2.4/1000 — BREACHED"],
    "feedback_summary": "Sentiment -0.26, 54% negative...",
    "debate_resolution": "Risk agent evidence outweighs PM recovery narrative."
  },
  "confidence": {
    "weighted_score": 87,
    "interpretation": "High confidence — strong evidence supports the verdict.",
    "verdict_distribution": {"ROLL_BACK": 3, "PAUSE": 2},
    "agreement_ratio": 0.6,
    "boosters": ["3+ consecutive improving days would confirm patch..."]
  },
  "risk_register": [
    {
      "title": "iOS crash causing data loss",
      "rating": "critical",
      "mitigation": "Rollback feature flag immediately",
      "owner": "Mobile Team"
    }
  ],
  "action_plan": {
    "immediate": [{"action": "Toggle SMARTDASH_V2 to OFF", "owner": "Engineering", "priority": "P0"}],
    "within_24h": [{"action": "Root cause analysis on iOS crash", "owner": "Mobile Team", "priority": "P1"}],
    "within_48h": [{"action": "Re-migration script for dashboard configs", "owner": "Data Engineering", "priority": "P2"}]
  },
  "communication_plan": {
    "internal_message": "SmartDash 2.0 rolled back due to 3 SLO breaches.",
    "user_message": "We identified issues with our recent update and reverted for stability.",
    "enterprise_message": "Our team is personally reaching out to discuss impact."
  },
  "debate_summary": {
    "tension": "PM argues recovery justifies PAUSE; Risk demands ROLL_BACK on payment integrity.",
    "resolved_verdict": "ROLL_BACK",
    "resolved_confidence": 92
  },
  "session_stats": {
    "total_agents": 5,
    "verdict_tally": {"ROLL_BACK": 3, "PAUSE": 2},
    "avg_confidence": 87.0
  }
}
```

---

## API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### REST endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server status + model info |
| `GET` | `/health/ready` | Readiness check (API key configured?) |
| `POST` | `/api/v1/warroom/run` | Run full war room, returns complete decision |
| `GET` | `/api/v1/warroom/sessions` | List all completed sessions |
| `GET` | `/api/v1/warroom/report/{session_id}` | Get full report for a session |
| `POST` | `/api/v1/monitor/ask` | Ask the monitor a question about a session |

### WebSocket

```
WS ws://localhost:8000/api/v1/warroom/stream
```

Streams live war room events. Event types:

| Event | Payload |
|---|---|
| `session_start` | `session_id`, `product` |
| `phase_start` | `number`, `title` |
| `agent_start` | `agent`, `tools` |
| `agent_verdict` | `agent`, `verdict`, `confidence`, `summary` |
| `debate_start` | — |
| `debate_resolved` | `resolved_verdict`, `resolved_confidence`, `ruling` |
| `final_decision` | `decision`, `confidence`, `tally`, `top_risks` |
| `complete` | `session_id`, `report_paths` |
| `error` | `message` |

### Example: run via curl

```bash
# Run a war room
curl -X POST http://localhost:8000/api/v1/warroom/run \
  -H "Content-Type: application/json" \
  -d '{"monitor_question": "What were the top risks?"}'

# Ask the monitor
curl -X POST http://localhost:8000/api/v1/monitor/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "b5cd075e", "question": "What did the Risk agent say?"}'
```

---

## Tests

```bash
cd backend
pytest tests/ -v
```

```
112 passed in 0.09s
```

| File | Tests | Covers |
|---|---|---|
| `test_tools.py` | 39 | All 5 tool functions against real mock data |
| `test_agents.py` | 32 | All 7 agents — structure, JSON parsing, report fields |
| `test_orchestrator.py` | 41 | Session memory, confidence scorer, output layer, data layer |

Tests use a mocked Groq client — no API key required to run the test suite.

---

## Project Structure

```
KairosAI/
│
├── backend/
│   ├── main.py                    # CLI entry point
│   ├── config.py                  # Settings via pydantic-settings
│   │
│   ├── data/                      # Mock dashboard inputs
│   │   ├── metrics.py             # 10-day KPI time series
│   │   ├── feedback.py            # 35 user feedback entries
│   │   └── release_notes.py       # Feature brief + known issues
│   │
│   ├── tools/                     # Pure Python tool functions
│   │   ├── aggregate_metrics.py
│   │   ├── detect_anomalies.py
│   │   ├── sentiment_analyzer.py
│   │   ├── trend_compare.py
│   │   └── risk_scorer.py
│   │
│   ├── agents/                    # AI agent personas
│   │   ├── base.py                # Shared base class + Groq client
│   │   ├── pm.py                  # Product Manager
│   │   ├── analyst.py             # Data Analyst
│   │   ├── marketing.py           # Marketing / Comms
│   │   ├── risk.py                # Risk / Critic
│   │   ├── sre.py                 # SRE / Engineering
│   │   ├── monitor.py             # War Room Monitor
│   │   └── moderator.py           # Debate Moderator
│   │
│   ├── core/                      # Orchestration engine
│   │   ├── orchestrator.py        # Runs all phases, synthesises decision
│   │   ├── debate_engine.py       # Structured challenge round
│   │   ├── confidence_scorer.py   # Weighted confidence calculation
│   │   └── session_memory.py      # Append-only event log
│   │
│   ├── api/                       # FastAPI application
│   │   ├── app.py                 # App factory + CORS
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── routes/
│   │       ├── warroom.py         # REST + WebSocket endpoints
│   │       ├── monitor.py         # Monitor Q&A endpoint
│   │       └── health.py          # Health checks
│   │
│   ├── output/                    # Report generation
│   │   ├── json_writer.py
│   │   ├── markdown_writer.py
│   │   ├── trace_logger.py
│   │   └── report_builder.py
│   │
│   └── tests/
│       ├── conftest.py            # Shared fixtures + mock Groq client
│       ├── test_tools.py
│       ├── test_agents.py
│       └── test_orchestrator.py
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── LaunchRoom.jsx     # War room UI with live streaming
│       │   ├── Dashboard.jsx      # KPI charts + feedback analysis
│       │   └── Reports.jsx        # Session browser + downloads
│       ├── components/            # AgentCard, DecisionPanel, TraceLog, etc.
│       └── services/              # API calls + WebSocket client
│
├── reports/                       # Generated JSON + MD reports (gitignored)
├── logs/                          # Runtime trace logs (gitignored)
├── .env.example                   # Environment variable template
├── requirements.txt               # Python dependencies
└── docker-compose.yml             # One-command full stack
```

---

## Docker

```bash
# Full stack (backend + frontend)
docker-compose up

# Backend only
cd backend && docker build -t kairosai-backend .
docker run -p 8000:8000 --env-file .env kairosai-backend
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
GROQ_API_KEY=gsk_...                        # Get free at console.groq.com

# Optional
GROQ_MODEL=llama-3.3-70b-versatile          # Default model
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
REPORTS_DIR=./reports
LOGS_DIR=./logs
```

---

## Mock Data

The war room runs against a realistic 10-day scenario for PurpleMerit's SmartDash 2.0 launch:

| KPI | Baseline | Peak degradation | Current | Status |
|---|---|---|---|---|
| Crash rate | 0.8/1k | 3.1/1k (+288%) | 2.4/1k | ⚠️ WARN |
| p95 latency | 210ms | 412ms (+96%) | 352ms | 🔴 CRITICAL |
| D1 retention | 61.8% | 53.8% (-8pp) | 56.0% | ⚠️ WARN |
| Payment success | 99.1% | 95.8% (-3.3pp) | 96.7% | ⚠️ WARN |
| Support tickets | 31/day | 163/day (+426%) | 128/day | 🔴 CRITICAL |

35 user feedback entries: 54% negative · 17% neutral · 29% positive.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with ⚡ by KairosAI — the right decision at the right moment</sub>
</div>

---

## Enhancements & Future Scope

KairosAI is architected for extensibility. The following enhancements represent the natural evolution of the platform from a single-session war room into a continuous, cloud-native launch intelligence system.

---

### 1. Cloud Feedback Pipeline

**Current state:** User feedback is a static 35-entry mock dataset embedded in `data/feedback.py`.

**Enhancement:** Replace the mock with a live ingestion pipeline that collects real user feedback from all channels continuously.

```
App Store Reviews  ─┐
Play Store Reviews  ├─→  Ingestion Service  →  Cloud Storage  →  KairosAI
Support Tickets     │     (Kafka / SQS)         (MongoDB Atlas      Feedback
Twitter / Reddit   ─┘                            / Firestore)        Tool
```

**Implementation plan:**

- **Ingestion layer:** Use Apache Kafka or AWS SQS as the message bus. Each feedback channel (App Store, Zendesk, Twitter API v2, Reddit PRAW) publishes events to a dedicated topic.
- **Storage layer:** MongoDB Atlas for structured feedback documents with metadata (source, timestamp, user tier, sentiment pre-score). Qdrant for vector embeddings enabling semantic search across feedback history.
- **Schema:** Extend the existing `FeedbackEntry` TypedDict with `embedding`, `product_version`, `region`, `device_os` fields.
- **KairosAI integration:** Replace `data/feedback.py` with a `FeedbackRepository` class that queries MongoDB for the most recent N entries within the launch window.

```python
# Future interface
from db.feedback_repository import FeedbackRepository

class SentimentAnalyzerTool:
    def run(self, launch_id: str, hours: int = 24) -> dict:
        repo = FeedbackRepository()
        entries = repo.get_recent(launch_id=launch_id, hours=hours)
        return self._analyse(entries)
```

**Cloud stack:** MongoDB Atlas · Apache Kafka · AWS SQS · Qdrant · Google Cloud Pub/Sub

---

### 2. Real-Time Feedback Streaming to KairosAI

**Current state:** The war room runs once on a static snapshot. It cannot detect when new critical feedback arrives after the session completes.

**Enhancement:** A continuous streaming pipeline that monitors incoming feedback and automatically triggers a new war room session — or alerts the Monitor agent — when sentiment crosses a threshold.

```
New Feedback Event
        │
        ▼
  Stream Processor          Threshold Check
  (Kafka Consumer)   →   (sentiment score < -0.4   →  Trigger War Room
                           OR churn signal detected)    Alert Monitor
                           OR critical keyword match)
```

**Implementation plan:**

- **Stream processor:** A Kafka consumer group that processes each new feedback event in real time. Uses a sliding window (e.g. last 500 events, last 2 hours) to compute a rolling sentiment score.
- **Threshold engine:** Configurable rules — e.g. "if rolling sentiment drops below -0.35 OR 3+ churn signals in 1 hour → trigger alert". Rules stored in a config YAML and hot-reloadable.
- **KairosAI integration:** The processor calls `POST /api/v1/warroom/run` automatically when thresholds are breached, or sends a WebSocket push to the Monitor agent with a summary of the incoming signal.
- **Scheduling:** For lower-urgency updates, a cron job (APScheduler or Celery Beat) runs `sentiment_analyzer()` every 15 minutes and appends the delta to the Monitor's session memory.

```python
# Future interface — scheduled feedback ingestion
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", minutes=15)
async def ingest_new_feedback():
    new_entries = await feedback_stream.poll_since(last_run)
    monitor.ingest_feedback_batch(new_entries)
    if monitor.sentiment_delta() < -0.15:
        await trigger_war_room(reason="sentiment_degradation")
```

**Cloud stack:** Apache Kafka · Celery + Redis · APScheduler · AWS Lambda · Webhooks

---

### 3. Cloud Report & Dashboard Storage

**Current state:** Reports are written to a local `backend/reports/` directory as JSON and Markdown files. Dashboards are rendered from hardcoded mock data in the React frontend.

**Enhancement:** Persist every war room session and its full report to cloud storage, with a queryable history and a live dashboard that pulls real metrics from a time-series database.

```
War Room Session
        │
        ├─→  MongoDB Atlas          (session metadata, agent verdicts, decisions)
        ├─→  AWS S3 / GCS           (full JSON + Markdown reports, immutable)
        ├─→  TimescaleDB / InfluxDB  (KPI time series for live dashboard)
        └─→  Grafana / Metabase      (real-time dashboard, exportable)
```

**Implementation plan:**

- **Session persistence:** After each war room, the `ReportBuilder` additionally writes to MongoDB Atlas. Schema: `sessions` collection with session metadata, agent verdicts, confidence score, decision, and S3 report URL.
- **Object storage:** Full JSON and Markdown reports uploaded to AWS S3 or Google Cloud Storage with a signed URL returned to the frontend for download. Reports are versioned and never overwritten.
- **Time-series metrics:** Each KPI data point from `metrics.py` ingested into TimescaleDB (PostgreSQL extension) or InfluxDB. The React `Dashboard.jsx` replaces hardcoded data with live API calls to a `/api/v1/metrics` endpoint.
- **Analytics dashboard:** Grafana pre-built dashboards showing KPI trends, decision history, agent confidence over time, and sentiment trajectory across multiple launches.
- **Reports page:** The `Reports.jsx` page gains pagination, search by date/decision/product, and one-click PDF export via a serverless function.

```python
# Future interface — cloud report persistence
class CloudReportBuilder:
    def build(self, decision: dict) -> dict:
        # existing local write
        paths = write_local(decision)
        # cloud uploads
        s3_url  = self.s3.upload(paths["json_report"])
        mongo_id = self.mongo.sessions.insert_one({
            "session_id": decision["meta"]["session_id"],
            "decision":   decision["decision"],
            "confidence": decision["confidence"]["weighted_score"],
            "agents":     decision["agent_verdicts"],
            "report_url": s3_url,
            "created_at": datetime.now(timezone.utc),
        })
        return {**paths, "s3_url": s3_url, "mongo_id": str(mongo_id)}
```

**Cloud stack:** MongoDB Atlas · AWS S3 / GCS · TimescaleDB · InfluxDB · Grafana · Metabase

---

### 4. Enhanced Agent Roster

**Current state:** 5 core agents + War Room Monitor + Debate Moderator.

**Enhancement:** Add specialised agents to cover the full range of launch risk — financial, legal, customer success, competitive, and infrastructure.

---

#### Finance Agent

**Role:** Quantifies the revenue impact of the launch decision in dollar terms.

```python
class FinanceAgent(BaseAgent):
    name = "Finance"
    role = "Finance — revenue impact, ARR risk, CAC/LTV effects"
    tools_to_use = ["revenue_impact_calculator", "churn_cost_estimator"]

    system_prompt = """You are the Finance lead in the war room.
    Translate metric degradation into revenue terms:
    - What is the projected ARR impact of current churn rate?
    - What is the cost of each duplicate payment charge?
    - What is the customer acquisition cost of re-winning churned users?
    - What is the revenue risk of proceeding vs rolling back?
    Always express findings in dollar figures, not just percentages."""
```

**Tools used:** `revenue_impact_calculator` (ARR × churn delta), `refund_cost_estimator` (payment failures × avg order value), `cac_recovery_estimator`.

---

#### Legal & Compliance Agent

**Role:** Flags regulatory exposure from payment failures, data issues, and SLA breaches.

```python
class LegalAgent(BaseAgent):
    name = "Legal / Compliance"
    role = "Legal — regulatory risk, SLA breach, data integrity liability"
    tools_to_use = ["sla_breach_detector", "gdpr_risk_scorer"]

    system_prompt = """You are the Legal & Compliance advisor in the war room.
    Your job is to flag legal exposure that the business may not see in the metrics:
    - Duplicate charges are potential UDAAP violations (US) / PSD2 violations (EU)
    - Data migration failures may constitute a GDPR data integrity breach
    - SLA breaches on enterprise contracts may trigger penalty clauses
    - iOS crashes may expose the company to App Store ToS violations
    Always recommend specific remediation steps to reduce legal exposure."""
```

**Tools used:** `sla_breach_detector` (checks enterprise SLA thresholds), `gdpr_risk_scorer` (data exposure scoring), `regulatory_flag_lookup`.

---

#### Customer Success Agent

**Role:** Focuses exclusively on high-value and enterprise account impact.

```python
class CustomerSuccessAgent(BaseAgent):
    name = "Customer Success"
    role = "Customer Success — enterprise account risk, NPS impact, churn prevention"
    tools_to_use = ["enterprise_impact_scorer", "nps_trend_analyzer"]

    system_prompt = """You are the Customer Success lead in the war room.
    Enterprise accounts (>$50k ARR) require immediate personal intervention.
    Your job:
    - Identify which enterprise accounts are affected by the current issues
    - Estimate NPS impact based on negative feedback volume and severity
    - Recommend specific outreach actions: call, email, SLA credit offer
    - Flag any accounts at risk of contract non-renewal within 90 days."""
```

---

#### Competitive Intelligence Agent

**Role:** Monitors whether competitors are capitalising on the launch degradation.

```python
class CompetitiveAgent(BaseAgent):
    name = "Competitive Intelligence"
    role = "Competitive — market positioning risk during launch degradation"
    tools_to_use = ["competitor_mention_tracker", "market_sentiment_scanner"]

    system_prompt = """You are the Competitive Intelligence analyst in the war room.
    A degraded launch is an opportunity for competitors. Your job:
    - Are competitors mentioning our issues on social media or review sites?
    - Are churning users explicitly mentioning switching to a competitor?
    - Is this the right moment to hold, or does speed of rollback matter for PR?
    - What is the competitive cost of a public incident vs a quiet rollback?"""
```

---

#### SRE Escalation Agent (Tier 2)

**Role:** A second SRE agent that goes deeper into root cause — reads error logs, traces, and incident timelines.

```python
class SREEscalationAgent(BaseAgent):
    name = "SRE Escalation"
    role = "SRE Tier 2 — deep root cause, incident timeline, fix feasibility"
    tools_to_use = ["error_log_analyzer", "trace_profiler", "fix_feasibility_scorer"]

    system_prompt = """You are the senior SRE called in for escalation.
    The on-call SRE has flagged 3 simultaneous SLO breaches. Your job:
    - Confirm the root cause hypothesis with log-level evidence
    - Estimate time to fix if we pause vs rollback
    - Is a targeted hotfix feasible in <4 hours or do we need full rollback?
    - What are the infra-level rollback risks (data loss, cache invalidation)?"""
```

---

### 5. Enhanced & Advanced Tools

**Current state:** 5 tools covering metrics aggregation, anomaly detection, sentiment analysis, trend comparison, and risk scoring.

**Enhancement:** A richer toolbox covering financial modelling, competitive signals, infrastructure deep-dives, predictive forecasting, and external data enrichment.

---

| Tool | Description | Used by |
|---|---|---|
| `revenue_impact_calculator` | Converts churn delta + payment failures into projected ARR loss | Finance Agent |
| `sla_breach_detector` | Checks enterprise SLA thresholds against current KPIs, returns breach count + penalty exposure | Legal Agent |
| `enterprise_impact_scorer` | Cross-references negative feedback with enterprise account list, returns impacted ARR | CS Agent |
| `nps_trend_analyzer` | Estimates NPS delta based on sentiment volume and severity weights | CS Agent |
| `fix_feasibility_scorer` | Scores hotfix vs rollback based on known issue complexity and team capacity | SRE Escalation |
| `error_log_analyzer` | Parses structured error logs (JSON/ELK) for crash signatures and frequency spikes | SRE Escalation |
| `competitor_mention_tracker` | Scans Twitter, Reddit, G2, Capterra for competitor mentions referencing our incident | Competitive Agent |
| `predictive_churn_model` | Uses historical churn curves to forecast 7-day and 30-day churn if current trajectory continues | Risk Agent, PM Agent |
| `cohort_retention_analyzer` | Breaks D1/D7 retention by acquisition cohort, device, and region to isolate affected segments | Data Analyst |
| `payment_audit_tool` | Queries Stripe webhook logs to count actual duplicate charges vs failed payment events | Legal Agent, Finance Agent |
| `historical_benchmark_lookup` | Compares current KPI degradation against past launches to contextualise severity | Data Analyst, PM Agent |
| `feature_flag_impact_analyzer` | Determines which percentage of users have the feature enabled and correlates with KPI degradation | SRE Agent |
| `infra_cost_monitor` | Tracks real-time cloud spend spikes caused by the N+1 query overload | Finance Agent, SRE Agent |
| `regulatory_flag_lookup` | Checks jurisdiction-specific regulations applicable to payment failures and data integrity issues | Legal Agent |
| `a_b_test_significance_checker` | Validates whether KPI changes are statistically significant or within normal launch variance | Data Analyst |
| `rollback_impact_predictor` | Predicts user experience during and after rollback (expected recovery timeline, data risks) | Risk Agent, PM Agent |

---
### A major Improvement I wanna add to this project in future ( confidence score updation for each agent based on the kind of feedback we received (tech issues, marketing issues, etc) based on issues we get the particular agent who is more capable of the issues analysis/solve can get more decision weightage intially. Thatwill helps in better solving of the issue


__
### Roadmap Summary

```
Current (v1.0)          Near-term (v1.5)             Long-term (v2.0)
─────────────────        ──────────────────────        ──────────────────────────
Static mock data    →    Live feedback pipeline    →   Multi-product war rooms
5 core agents       →    +4 specialised agents     →   Agent marketplace
Local reports       →    Cloud report storage      →   Executive dashboards
One-shot session    →    Continuous monitoring     →   Predictive launch scoring
REST + WebSocket    →    Real-time streaming       →   Slack / Teams integration
Manual trigger      →    Auto-trigger on alerts    →   CI/CD pipeline gate
```
