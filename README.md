# O2C Intelligence

> AI-powered Order-to-Cash analytics platform for SAP data — built to surface operational bottlenecks, flag financial risk, and answer natural language questions grounded in real transaction data.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/frontend-Vanilla%20JS-f7df1e?style=flat-square&logo=javascript&logoColor=black)
![Stack](https://img.shields.io/badge/database-Firebase%20Firestore-orange?style=flat-square&logo=firebase&logoColor=white)
![Stack](https://img.shields.io/badge/AI-Gemini%20%2F%20OpenRouter%20%2F%20Groq-blueviolet?style=flat-square)
![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20e2e-brightgreen?style=flat-square)

**[→ View the live demo](https://dodgetask.netlify.app/)**

---

## What it does

O2C Intelligence ingests raw SAP JSONL exports across 11 source tables and produces a live analytics platform covering the full order lifecycle — Sales Order → Delivery → Billing → Payment → Journal Entry. The system automatically detects operational failures, quantifies revenue leakage, and lets analysts interrogate any order or customer through a conversational AI layer.

---

## Features

### KPI Dashboard
Aggregated metrics computed from the unified dataset: total revenue, Days Sales Outstanding, collection rate, average cycle times per stage (order→delivery, delivery→billing, billing→payment), and per-issue-type breakdowns. Numbers update from the in-memory DataFrame on every request — no pre-baked stale snapshots.

### Order Lifecycle Tracker
Every order exposes its `lifecycle_stage` (`ordered → delivered → billed → paid → cancelled`), derived at pipeline time from which downstream documents actually exist in the data. The stage is deterministic — it is not a field stored in SAP, it is computed from the join graph.

### Relationship View
Interactive document graph for any order. Nodes represent SAP documents (Sales Order, Delivery, Billing Doc, Payment/Accounting Document, Journal Entry) and edges represent the join keys used to link them. Shows exactly where a transaction chain breaks — e.g. a delivery exists but no billing doc was ever created.

### Automated Issue Detection
Five rule-based flags are evaluated per order at pipeline time and stored as boolean columns. No LLM is involved in flagging:

| Flag | Field | Rule |
|---|---|---|
| Delivery Delay | `is_delivery_delayed` | `order_to_delivery_days > 3` |
| Payment Overdue | `is_payment_overdue` | `billing_to_payment_days > payment_term_days` (Z001=30, Z009=0) |
| Unpaid Invoice | `is_unpaid` | billing doc exists, payment does not, not cancelled |
| Billing Cancelled | `is_billing_cancelled` | cancellation record found in `billing_document_cancellations` |
| Missing Stage | `missing_stage` | no delivery, or delivery exists but no billing doc |

Each order also receives an additive `issue_severity` score (0–5). The `/api/issues` endpoint returns orders sorted by severity descending with human-readable `issue_labels` annotations attached at query time.

### Customer Intelligence
Per-customer KPIs including `risk_score`, cancellation rate, unpaid invoice count, and cycle time averages. Customers are sorted by risk score at the API level, making it easy to surface the most problematic accounts first.

### AI Chat — Multi-Model System
Natural language interface over the O2C dataset. Described in detail below.

---

## AI Layer

The AI layer is built around three concepts: **use-case routing**, **automatic fallback**, and **grounded prompting**. There is no single "AI endpoint" — each query type is treated as a distinct use case with its own model assignment and prompt template.

### Use-case routing

`llm_router.py` routes each request based on the declared `use_case`:

| Use case | Primary | Fallback chain | Rationale |
|---|---|---|---|
| `nl_query` | Gemini | → Groq → OpenRouter | Conversational; needs strong context retention |
| `root_cause` | OpenRouter (Claude) | → Gemini → Groq | Multi-step causal reasoning over structured order data |
| `insights_summary` | Groq (LLaMA) | → Gemini → OpenRouter | Batch summarisation; prioritise speed and cost |
| `recommendations` | Gemini | → OpenRouter → Groq | Synthesis of actionable guidance |
| `delay_analysis` | — | full chain | Pattern analysis across the dataset |
| `customer_risk` | — | full chain | Per-customer risk narrative |

The caller can also pass a `preferred_model` override to pin a specific provider for a single request.

### Fallback mechanism

Every use case has an ordered provider chain. If a provider raises any exception — rate limit, timeout, missing API key, or network error — the router logs a warning and tries the next provider automatically. All errors are collected; if every provider fails, a `RuntimeError` is raised with the full error list, which the endpoint converts to an HTTP 503. The user never sees a raw provider error.

```python
# From llm_router.py — simplified
for model_name in chain:
    try:
        response = await client(prompt)
        return response, model_name
    except Exception as e:
        errors.append(f"{model_name}: {e}")
raise RuntimeError(f"All providers failed: {' | '.join(errors)}")
```

### Grounded prompting

Every prompt receives a `_dataset_context()` block injected at build time — key statistics pulled live from the in-memory KPI snapshot (total orders, revenue, cancellation rate, cycle times, issue counts). This means the LLM is always working from accurate numbers without needing the full CSV in the prompt window.

Prompt templates in `prompts.py` are structured per use case:

- `nl_query` — direct question + dataset context, instructs the model to reference actual numbers
- `root_cause` — full order header JSON + items JSON, asks for 2–3 sentence analysis and a numbered recommendation list. The router post-processes the response to split `analysis` from `recommendations` for clean structured output.
- `insights_summary` — instructs the model to return **exactly** a JSON array with `title`, `summary`, `recommendation`, `severity` fields. The parser strips markdown fences, finds the `[...]` block, and falls back to a wrapped single insight if the JSON is malformed.
- `customer_risk` — customer KPI dict, requests risk summary + top risk factors + mitigation actions
- `delay_analysis` — dataset-wide delay pattern analysis with a financial impact focus

The system prompt establishes the model as an SAP SD/O2C specialist, specifying the org code (`ABCD`), currency (`INR`), and output format expectations (concise, data-referenced, actionable).

### Guardrails

Several layers restrict misuse and off-topic prompts:

**Input validation via Pydantic** — `QueryRequest` enforces `min_length=3, max_length=1000` on question fields. An empty or too-short question returns HTTP 422 before any LLM call is made. A missing `order_id` in a root cause request also fails fast with 422.

**Domain anchoring in every prompt** — the system prompt explicitly identifies the model as an O2C analyst for a specific SAP dataset. Combined with the injected dataset context, this strongly biases responses toward the actual data and discourages hallucinated generalisations.

**Entity existence checks before AI calls** — root cause analysis and customer risk endpoints validate that the requested order or customer exists in the dataset and return HTTP 404 before spending a token if not:
```python
context = await get_order_context(req.order_id)
if not context.get("order"):
    raise HTTPException(status_code=404, detail=f"Order {req.order_id} not found")
```

**Response caching** — repeated identical questions return cached answers rather than re-querying the LLM. The cache key is derived from the question text (first 80 chars) or the entity ID. This also prevents prompt-replay abuse from saturating provider rate limits.

**Firestore persistence** — every query and generated insight is persisted to Firestore. The insights endpoint checks Firestore before calling the LLM, meaning insights are only generated once per cycle unless a `?refresh=true` flag is explicitly passed. This is both a cost guardrail and a tamper-detection mechanism.

**Fallback output format** — `parse_insights_json` has a three-tier fallback (parse `[...]` block → parse whole string → wrap raw text). Even a completely unstructured LLM response will return a valid API response rather than a 500.

---

## Data model and graph structure

### Source tables (11 SAP JSONL feeds)

The pipeline loads 11 raw SAP table exports from JSONL part-files and joins them into a single analytical table.

```
sales_order_headers          ─┐
sales_order_items             ├─ Base fact (one row per order item)
sales_order_schedule_lines   ─┘
        │
        │ sales_order_id + item (normalised, leading zeros stripped)
        ▼
outbound_delivery_items ──── outbound_delivery_headers
        │
        │ delivery_id
        ▼
billing_document_items (agg by delivery_id)
        │
        │ billing_doc_id
        ▼
billing_document_headers ◄── billing_document_cancellations
        │
        │ accounting_document
        ▼
payments_accounts_receivable (agg by accounting_document)
journal_entry_items_accounts_receivable

Enrichment:
business_partners          → customer_name
products + product_descriptions → material_desc
```

The join chain mirrors the actual SAP document flow. Left joins are used throughout so orders with no downstream document (e.g. an order placed but never delivered) are preserved with NULLs, enabling `missing_stage` detection. Item numbers are normalised by stripping leading zeros before matching across tables, handling a real SAP formatting inconsistency in the source data.

### Output tables

| File | Grain | Purpose |
|---|---|---|
| `unified_o2c.csv` | One row per (sales_order_id, sales_order_item) | Full-detail analytics, AI context for root cause |
| `unified_o2c_orders.csv` | One row per sales_order_id | Dashboard queries, issue detection, API responses |
| `kpi_summary.json` | Singleton | Pre-computed top-level KPIs injected into every AI prompt |
| `customer_kpis.json` | One object per customer | Customer intelligence page, customer risk AI |

### Lifecycle stage derivation

`lifecycle_stage` is not a field in SAP — it is computed at pipeline time from the presence or absence of downstream documents:

```python
def derive_stage(row):
    if row.get("is_cancelled"):       return "cancelled"
    if pd.notna(row["payment_posting_date"]): return "paid"
    if pd.notna(row["billing_doc_id"]):       return "billed"
    if pd.notna(row["delivery_id"]):          return "delivered"
    return "ordered"
```

This produces a deterministic, auditable stage for every order without relying on SAP status fields that can be inconsistently populated.

### Severity scoring

Each order receives an additive `issue_severity` score (0–5) summing the boolean issue flags. This single integer enables fast severity-based sorting and filtering across the API without recomputing flag logic on every request.

---

## Code architecture

### Backend structure

```
backend/
├── main.py                  # FastAPI app, CORS, timing middleware, lifespan
└── app/
    ├── ai/
    │   ├── llm_router.py    # Use-case routing, fallback chain, JSON parsing
    │   ├── prompts.py       # All prompt templates + live dataset context injection
    │   ├── gemini_client.py
    │   ├── groq_client.py
    │   └── openrouter_client.py
    ├── models/              # Pydantic schemas (Order, Customer, KPI, AI request/response)
    ├── routers/             # One router per domain (kpis, orders, issues, customers, ai)
    ├── services/
    │   ├── data_service.py  # In-memory DataFrame queries — all API data access goes here
    │   ├── issue_service.py # Issue filtering, severity sorting, label annotation
    │   ├── kpi_service.py   # KPI aggregation and customer risk scoring
    │   ├── firebase_service.py # Firestore persistence (queries, insights)
    │   └── cache_service.py # TTL cache — cachetools with dict fallback
    ├── utils/
    │   ├── date_utils.py
    │   └── formatters.py
    └── config.py            # AI routing table, thresholds, paths
```

**Design principles:**

- **Single data load, all reads from memory.** `DataService.load()` is called once at startup via FastAPI's `lifespan` context manager. All subsequent queries operate on the in-memory DataFrames — no per-request file I/O. The `_ensure_loaded()` guard makes any service call safe regardless of startup order.

- **Thin routers, logic in services.** Routers handle HTTP concerns (request parsing, error codes, response shaping). Business logic lives in services. The AI router is ~100 lines and delegates everything to `llm_router` and `data_service`.

- **Cache-then-Firestore-then-LLM.** The insights endpoint checks the in-memory cache first, then Firestore, and only calls the LLM as a last resort. This three-tier pattern minimises cost and latency for repeat requests.

- **Structured logging.** Every request is logged with method, path, status, and processing time via a timing middleware. The AI router logs each provider attempt and outcome. Log names follow a `o2c.*` hierarchy for easy filtering.

### Frontend structure

```
frontend/
├── index.html               # Single-file dashboard entry point
├── relationship-view.html   # Document graph explorer
└── src/
    ├── components/
    │   ├── ai/              # ChatInterface, RootCausePanel, RecommendationPanel, InsightCard
    │   ├── dashboard/       # KPIGrid, RevenueChart, CycleTimeChart, StageDistribution
    │   ├── issues/          # IssuePanel, IssueRow, SeverityBadge, DelayHeatmap
    │   ├── lifecycle/       # OrderTable, OrderDetailDrawer, LifecycleFlow, StageStepper
    │   └── shared/          # Badge, FilterBar, KPICard, Sidebar, Spinner, Topbar
    ├── pages/               # Dashboard, Lifecycle, Issues, Customers, AIInsights
    ├── services/api.js      # Centralised fetch wrapper
    ├── styles/              # variables.css, globals.css, components.css
    └── utils/               # formatters.js, dateUtils.js, colors.js
```

The frontend is fully static by default — pages load from pre-processed CSV/JSON files served alongside the HTML, with no backend dependency for read operations. AI features and any write operations route through FastAPI.

---

## Storage architecture and tradeoffs

| Layer | Technology | Rationale |
|---|---|---|
| Primary query store | Pandas DataFrames in memory | Zero-latency reads; dataset fits in memory; no query translation needed |
| Persistent store | Firebase Firestore | Serverless, no ops overhead; used for AI query history and insight persistence only |
| Cache | `cachetools` TTLCache (512 entries) | Prevents duplicate LLM calls; auto-expires stale results. Falls back to a plain dict implementation if `cachetools` is not installed |
| Pre-computed outputs | CSV + JSON files | Pipeline outputs are committed alongside the app so the frontend can run entirely without a backend |

The intentional design choice here is to treat Firestore as a **write-ahead log and persistence layer**, not as a query database. All analytical queries run against in-memory DataFrames. This gives sub-millisecond response times for every data endpoint (verified in the performance test suite at < 2000ms threshold) while keeping infrastructure costs near zero.

---

## Testing

The test suite has two layers:

**Unit tests (`pytest`)** — `tests/test_ai.py` tests prompt construction and router logic with mock clients, verifying that: the correct fields appear in each prompt type, real dataset stats are injected, JSON parsing handles valid JSON, markdown-fenced JSON, and completely malformed output, and that the router raises `RuntimeError` with a full error list when all providers fail.

**End-to-end test suite (`e2e_test.py`)** — a self-contained HTTP test runner covering all 5 routers across 8 test groups (system, KPIs, orders, issues, customers, AI, edge cases, performance). Each test specifies expected HTTP status and a list of typed assertions (eq, gt, gte, in, exists, type, not_empty, ne) resolved via dot-path navigation into the JSON response. The suite outputs structured JSON results for CI integration.

```bash
# Run unit tests
cd backend && pytest tests/

# Run e2e tests (backend must be running)
python tests/e2e_test.py

# Include AI endpoints
python tests/e2e_test.py --test-ai

# Save results
python tests/e2e_test.py > results.json
```

Specific edge cases covered: empty question returns 422, unknown order/customer returns 404 with detail, non-existent lifecycle stage returns empty result set (not an error), pagination offsets correctly, combined multi-filter queries return intersected results, and high-severity filter correctly excludes lower-severity orders.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Chart.js |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Persistent store | Firebase Firestore |
| In-memory query layer | Pandas DataFrames |
| Cache | cachetools TTLCache (dict fallback) |
| AI | Gemini · OpenRouter (Claude) · Groq (LLaMA) — use-case routed with automatic fallback |
| Pipeline | Pandas ETL, 11 SAP JSONL sources |
| Tests | pytest, asyncio, custom E2E runner |

---

