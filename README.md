# O2C Intelligence

> AI-powered Order-to-Cash analytics platform for SAP data — built to surface bottlenecks, flag risks, and let you interrogate every order in plain English.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/frontend-Vanilla%20JS-f7df1e?style=flat-square&logo=javascript&logoColor=black)
![Stack](https://img.shields.io/badge/database-Firebase%20Firestore-orange?style=flat-square&logo=firebase&logoColor=white)
![Stack](https://img.shields.io/badge/AI-Gemini%20%2F%20OpenRouter%20%2F%20Groq-blueviolet?style=flat-square)

**[→ View the live demo](https://dodgetask.netlify.app/)**

---

## Features

### KPI Dashboard
Real-time metrics across the entire O2C pipeline — total revenue, Days Sales Outstanding (DSO), collection rate, average cycle times, and cancellation counts. Every number is computed from the unified SAP dataset and refreshes on load.

### Order Explorer
Browse and filter every sales order with lifecycle stage badges (`Ordered → Delivered → Billed → Paid`), risk scores, payment terms, and cycle time breakdowns. Click any order to drill into its full document chain.

### Automated Issue Detection
The platform continuously scans orders against a set of rules and flags anything anomalous:

| Flag | Condition |
|---|---|
| Delivery Delay | `order_to_delivery_days` exceeds threshold |
| Billing Delay | `delivery_to_billing_days` exceeds threshold |
| Unpaid Invoice | `is_unpaid = True` |
| Payment Overdue | `billing_to_payment_days > expected_payment_days` (per payment terms) |
| Billing Cancelled | `is_billing_cancelled = True` |
| Missing Stage | Order stuck with no downstream document (`missing_stage = True`) |

### Relationship View
An interactive document graph for any order — visualises the full chain from Sales Order through Delivery, Billing, Payment, and Journal Entry. Each node shows the document ID and key dates; edges show the join keys used (`referenceSdDocument`, `accountingDocument`).

### Customer Intelligence
Per-customer breakdown of payment behaviour, order history, cancellation rate, and outstanding balances — useful for spotting at-risk accounts before they become write-offs.

### Multi-Model AI Chat
Ask natural language questions about any order or the whole pipeline. The AI layer uses a **use-case-aware LLM router** that picks the right model for each query type:

| Query type | Primary model | Why |
|---|---|---|
| `nl_query` — conversational questions | Gemini | Best at dialogue and context retention |
| `root_cause` — why is this order delayed? | OpenRouter / Claude | Best at multi-step reasoning |
| `insights_summary` — pipeline-wide trends | Groq / LLaMA | Fastest and cheapest for summarisation |

Each use-case has an **ordered fallback chain** — if the primary provider hits a rate limit or timeout, the next is tried automatically. The system never surfaces a provider error to the user.

Answers are grounded in real order data and cite the specific rule or field that triggered each finding (e.g. `order_to_delivery_days (18) > 14d threshold`).

---

## Architecture

```
Frontend (HTML/CSS/JS)
        ↕  REST /api/*
FastAPI Backend
   ├── DataService     (Pandas in-memory cache of unified_o2c.csv)
   ├── LLM Router      (Gemini / OpenRouter / Groq — use-case routed with fallback)
   └── Firebase Firestore  (persistent store)
        ↕
Pandas ETL Pipeline
   SAP JSONL (raw) → unified_o2c.csv + kpi_summary.json
```

The frontend is fully static by default — pages load from pre-processed CSV/JSON for instant render with no backend required. AI features and write operations go through FastAPI.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Chart.js |
| Backend | Python, FastAPI, Uvicorn |
| Database | Firebase Firestore |
| Data | Pandas ETL → `unified_o2c.csv`, `kpi_summary.json`, `customer_kpis.json` |
| AI | Gemini · OpenRouter · Groq — use-case routed with automatic fallback |

---

## Project structure

```
o2c-intelligence/
├── frontend/
│   ├── index.html                  # Dashboard, orders, issues, AI chat
│   ├── relationship-view.html      # Document graph explorer
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── utils/
│
├── backend/
│   ├── main.py
│   └── app/
│       ├── ai/
│       │   ├── llm_router.py       # Use-case → model routing + fallback chain
│       │   ├── gemini_client.py
│       │   ├── groq_client.py
│       │   ├── openrouter_client.py
│       │   └── prompts.py
│       ├── models/                 # Pydantic schemas (order, customer, kpi, issue)
│       ├── routers/                # /api/kpis  orders  issues  customers  ai
│       └── services/               # DataService + business logic
│
├── pipeline/
│   └── o2c_pipeline.py             # SAP JSONL → unified CSV + KPI JSON
│
└── data/
    └── processed/
        ├── unified_o2c.csv         # Grain: one row per order line item
        ├── unified_o2c_orders.csv  # Grain: one row per order
        ├── kpi_summary.json
        └── customer_kpis.json
```

---
