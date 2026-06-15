# Stelos AI

**Industrial Predictive Maintenance Intelligence Platform**

Stelos AI is an autonomous AI layer built for the Tata Steel AI Hackathon 2026 (Agentic AI Challenge). It lives between a steel plant's raw sensor streams and the humans who make maintenance decisions — watching every critical machine continuously, predicting how many days remain before each one fails, diagnosing the root cause with cited evidence, pricing the financial risk in rupees, and routing the right work order to the right person before a single breakdown stops the line.

The guiding principle: the ML engines decide, RAG retrieves the evidence, and the LLM only explains. The AI never invents a diagnosis — it takes a deterministic, traceable conclusion from real models and puts it into plain English.

---

## Architecture

```
Sensor Data → Dynamic Health Engine → LangGraph 6-Agent Pipeline → Dashboard + Alerts
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              ▼               ▼               ▼               ▼               ▼               ▼
         Diagnostic    Knowledge        RootCause    Predictive     Business      Executive
           Agent       Retrieval          Agent      Maintenance     Impact      Intelligence
        (IF + XGB)    (FAISS RAG)       (LLM)        Agent (Weibull) (Finance)   (Narrator)
```

### Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 15, React 19, Tailwind CSS, Recharts, TypeScript |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic v2, APScheduler, WebSockets |
| **AI / ML** | LangGraph (multi-agent orchestration), Isolation Forest (anomaly detection), XGBoost + SHAP (fault classification, AI4I 2020 dataset), Weibull distribution (RUL physics model), FAISS (semantic vector retrieval) |
| **LLM** | Groq LLaMA-3.3-70b (primary), Google Gemini Flash (fallback) |
| **Vision** | Groq LLaMA-4 Scout (image-based damage description) |
| **Observability** | Prometheus metrics endpoint, structured agent trace logging |
| **Notifications** | Gmail SMTP (email reports), WebSocket (real-time alerts) |
| **Deployment** | Vercel (frontend), Docker (backend) |

---

## Agentic AI Pipeline (LangGraph)

A stateful 6-agent linear pipeline where each agent reads the shared `MaintenanceState` and writes its contribution before passing control to the next:

1. **Diagnostic Agent** — Isolation Forest anomaly detection + XGBoost/SHAP fault classification. Outputs severity: EMERGENCY / CRITICAL / WARNING / NORMAL. `llm_enhanced: true`
2. **KnowledgeRetrieval Agent** — FAISS semantic search over SOPs, equipment manuals, and incident history. Retrieves 4 most relevant documents per query.
3. **RootCause Agent** — Reasons over sensor evidence + retrieved SOPs. Outputs `root_cause`, `causal_chain`, `primary_mechanism`, `confidence`. `llm_enhanced: true`
4. **PredictiveMaintenance Agent** — Weibull RUL physics model predicts days-to-failure with confidence bounds. Generates 3–5 SOP-grounded work orders with part names, time estimates, and live inventory cross-check. `llm_generated_actions: true`
5. **BusinessImpact Agent** — Deterministic financial math: planned vs. emergency cost, production loss in ₹, ROI of acting now vs. delaying.
6. **ExecutiveIntelligence Agent** — Synthesises all 5 prior outputs into a plain-English executive narrative. LLM explains the already-decided conclusion; it cannot change it.

---

## Key Features

- **Autonomous Sentinel** — Background agent scanning all machines every 60 seconds via APScheduler, pushing WebSocket alerts on threshold breach with no human trigger.
- **Dynamic Health Engine** — Adaptive sensor weighting per equipment type (pump / furnace / conveyor), health state, and season. Not static thresholds.
- **Hybrid RAG** — FAISS semantic retrieval grounded in real SOPs and failure reports. Every diagnosis is cited, never hallucinated.
- **What-If Simulator** — 7-step ML pipeline simulation across 3 scenarios (act now / delay 7 days / delay 30 days) with financial outcomes and Recharts visualisation.
- **Maintenance Hub** — Logbook, Approvals (with live parts OOS flags + lead times), and Spare Parts inventory (19 parts, auto-restock urgency).
- **AI Copilot + Vision** — Chat interface for plain-English status queries. Image upload → Groq LLaMA-4 Scout describes visible damage.
- **Feedback Learning Loop** — Operator confirmations and corrections re-calibrate confidence scores over time.
- **PDF Report** — One-click export of live fleet data, health scores, RUL predictions, and financial exposure.
- **Prometheus Metrics** — `/metrics` endpoint for operational observability.
- **Email Reports** — Gmail SMTP delivery of maintenance summaries.

---

## Getting Started

### Docker (Full Stack)

```bash
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/docs`

### Development Mode

**Backend:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

```env
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

---

## Hackathon Submission Highlights

- Real ML models (Isolation Forest, XGBoost, Weibull) — no mock scoring.
- Every diagnosis is grounded in retrieved SOPs and cited by source.
- Full explainability: SHAP feature importance, causal chain, evidence trail, confidence score.
- Financial justification on every recommendation: ₹ downtime, ROI, planned vs. emergency cost ratio.
- Autonomous 24/7 monitoring with role-aware alert routing.
- Closed-loop procurement: failure timeline vs. part lead time, auto-restock urgency.
- Human feedback loop with measurable accuracy trend.
