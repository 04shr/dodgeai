# O2C Intelligence

> AI-powered Order-to-Cash analytics platform for SAP data — built to surface bottlenecks, flag risks, and answer questions about every order in your pipeline.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/frontend-Vanilla%20JS-f7df1e?style=flat-square&logo=javascript&logoColor=black)
![Stack](https://img.shields.io/badge/database-Firebase%20Firestore-orange?style=flat-square&logo=firebase&logoColor=white)
![Stack](https://img.shields.io/badge/AI-Gemini%20%2F%20OpenRouter%20%2F%20Groq-blueviolet?style=flat-square)

---

## What it does

O2C Intelligence ingests SAP order data and turns it into a live analytics dashboard with AI-assisted investigation. The platform covers the full order lifecycle — from sales order creation through delivery, billing, and payment — and automatically flags anything that looks wrong.

**Core capabilities:**

- **KPI Dashboard** — Revenue, DSO, collection rate, cycle times, cancellations, and more at a glance
- **Order Explorer** — Browse and filter every order with status badges, risk scores, and lifecycle stage tracking
- **Issue Detection** — Automatically surfaces delivery delays, billing gaps, unpaid invoices, cancelled documents, and missing stages using rule-based flags
- **Customer Intelligence** — Per-customer performance view with payment behaviour, order history, and risk profiling
- **Relationship View** — Interactive graph showing the document chain for any order (SO → Delivery → Billing → Payment → Journal)
- **AI Chat** — Ask natural language questions about any order or the overall pipeline; answers are grounded in your actual data with rule citations

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Frontend                        │
│  Vanilla HTML/CSS/JS  ·  Dark UI  ·  Chart.js       │
│  index.html (dashboard + AI)                        │
│  relationship-view.html (graph explorer)            │
└────────────────────────┬────────────────────────────┘
                         │ REST  /api/*
┌────────────────────────▼────────────────────────────┐
│                  FastAPI Backend                    │
│  /api/kpis   /api/orders   /api/issues              │
│  /api/customers            /api/ai                  │
│                                                     │
│  DataService  (in-memory Pandas cache)              │
│  Multi-LLM router  (Gemini → OpenRouter → Groq)     │
└───────────┬─────────────────────────┬───────────────┘
            │                         │
┌───────────▼──────────┐   ┌──────────▼──────────────┐
│  Firebase Firestore  │   │   ETL Pipeline          │
│  (persistent store)  │   │   pandas · o2c_pipeline  │
└──────────────────────┘   └─────────────────────────┘
```

**Tech stack:**

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Chart.js, Syne + IBM Plex Mono fonts |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | Firebase Firestore |
| Data processing | Pandas ETL pipeline |
| AI | Gemini (primary), OpenRouter, Groq (fallback chain) |

---

## Project structure

```
o2c-intelligence/
├── frontend/
│   ├── index.html              # Main dashboard (KPIs, orders, issues, AI chat)
│   └── relationship-view.html  # Document graph explorer
│
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   └── app/
│       ├── routers/
│       │   ├── kpis.py
│       │   ├── orders.py
│       │   ├── issues.py
│       │   ├── customers.py
│       │   └── ai.py
│       └── services/
│           └── data_service.py
│
├── pipeline/
│   └── o2c_pipeline.py         # Pandas ETL — SAP data → Firestore
│
└── README.md
```

---

## Getting started

### Prerequisites

- Python 3.11+
- A Firebase project with Firestore enabled
- API keys for at least one LLM provider (Gemini, OpenRouter, or Groq)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the `backend/` directory:

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccount.json

# LLM providers (add whichever you have)
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# CORS (optional, defaults to localhost:5173 and :8080)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```

### 3. Run the ETL pipeline

Loads and transforms your SAP export into Firestore:

```bash
cd pipeline
python o2c_pipeline.py
```

### 4. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 5. Serve the frontend

```bash
cd frontend
python -m http.server 5173
```

Open `http://localhost:5173` in your browser.

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server status and data load check |
| `GET` | `/api/kpis` | Aggregate KPIs (revenue, DSO, cycle times, etc.) |
| `GET` | `/api/orders` | Paginated order list with filters |
| `GET` | `/api/orders/{id}` | Single order detail with line items |
| `GET` | `/api/issues` | All flagged orders with issue type breakdown |
| `GET` | `/api/customers` | Customer-level performance summary |
| `POST` | `/api/ai/chat` | Natural language Q&A grounded in order data |

Full interactive docs available at `/docs` when the backend is running.

---

## Issue detection rules

The platform flags orders that match any of the following conditions:

| Flag | Rule |
|---|---|
| **Delivery Delay** | `order_to_delivery_days` exceeds threshold |
| **Billing Delay** | `delivery_to_billing_days` exceeds threshold |
| **Unpaid Invoice** | `is_unpaid = True` |
| **Payment Overdue** | `billing_to_payment_days > expected_payment_days` |
| **Billing Cancelled** | `is_billing_cancelled = True` |
| **Missing Stage** | `missing_stage = True` (order stuck with no downstream document) |

All flag thresholds are configurable in the pipeline config.

---

## AI chat

The AI endpoint accepts natural language questions about orders or the overall pipeline. It works in two modes:

- **Order-scoped** — Ask about a specific order ID (e.g. *"Why is order 4500012345 delayed?"*). The model receives the full document chain, cycle times, flags, and payment status as context, and cites the rule that triggered each answer.
- **Pipeline-wide** — Ask aggregate questions (e.g. *"Which customers have the most overdue invoices?"*). The model queries the in-memory dataset via the `/api/ai` router.

The LLM router tries Gemini first, then falls back to OpenRouter, then Groq, so the system stays up even if a provider has an outage.

---

## Development notes

- The `DataService` loads all order data into memory on startup for fast query performance. Call `DataService.load()` to reload without restarting.
- CORS is currently set to `allow_origins=["*"]` for local development. Lock this down before any production deployment.
- Request timing is logged automatically via middleware — check the `X-Process-Time-Ms` response header or server logs.

---
