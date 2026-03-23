"""
Prompt Templates
================
Each use-case gets a structured system + user prompt.
Real dataset statistics are injected so the LLM has accurate context
without needing the full CSV in the prompt window.
"""
import json
from app.services.data_service import _kpis

SYSTEM_BASE = """You are an expert O2C (Order-to-Cash) business intelligence analyst.
You specialise in SAP SD processes, enterprise finance, and operational KPIs.
The dataset is from a real SAP ECC system (org code ABCD, all transactions in INR).

When answering:
- Be specific and reference actual numbers from the data
- Identify root causes, not just symptoms
- Give actionable recommendations
- Keep answers concise (3–5 sentences for analysis, bullet points for recommendations)
- If data is insufficient for a conclusion, say so clearly"""


def _dataset_context() -> str:
    """Inline key stats so every prompt has grounding facts."""
    try:
        k = _kpis or {}
        o = k.get("overview", {})
        iss = k.get("issues", {})
        cy = k.get("cycle_times", {})
        return f"""
Current dataset snapshot (SAP ABCD, INR):
- {o.get('total_orders', 100)} orders | {o.get('unique_customers', 8)} customers
- Total ordered: ₹{o.get('total_revenue_inr', 70878):,.0f} | Paid: ₹{o.get('total_paid_inr', 43705):,.0f}
- Revenue leakage: ₹{o.get('revenue_leakage_inr', 27174):,.0f} ({100 - o.get('payment_coverage_pct', 62):.0f}% uncollected)
- Cancellation rate: {iss.get('cancellation_rate_pct', 56)}% ({iss.get('orders_billing_cancelled', 56)} orders)
- Unpaid invoices: {iss.get('orders_unpaid', 22)} | Missing stages: {iss.get('orders_missing_stage', 17)}
- Avg O2C cycle: {cy.get('avg_total_o2c_days', 6.84)} days | Avg delivery→billing: {cy.get('avg_delivery_to_billing_days', 3.84)} days
- Delivery delays: {iss.get('orders_with_delivery_delay', 9)} orders ({iss.get('delivery_delay_rate_pct', 9)}%)
"""
    except Exception:
        return "Dataset: 100 orders, 8 customers, INR, SAP ABCD. Cancellation rate: 56%. Avg O2C: 6.84 days."


def build_prompt(use_case: str, context: dict) -> str:
    ctx = _dataset_context()

    # ── Natural language query ────────────────────────────
    if use_case == "nl_query":
        return f"""{SYSTEM_BASE}
{ctx}
User question: {context.get('question', '')}

Answer directly and concisely. Reference specific data where relevant."""

    # ── Root cause analysis ───────────────────────────────
    if use_case == "root_cause":
        order_json = json.dumps(context.get("order", {}), indent=2, default=str)
        items_json = json.dumps(context.get("items", []), indent=2, default=str)
        return f"""{SYSTEM_BASE}
{ctx}
Analyse the following O2C order and identify any operational issues.

Order header:
{order_json}

Order items:
{items_json}

Provide:
1. A 2–3 sentence root cause analysis of any issues present
2. 2–3 specific, actionable recommendations
Format recommendations as a numbered list."""

    # ── System-wide insights ──────────────────────────────
    if use_case == "insights_summary":
        return f"""{SYSTEM_BASE}
{ctx}
Generate exactly 3 key business insights for this O2C dataset.

For each insight provide:
- title: short descriptive title (5–7 words)
- summary: 2 sentences explaining the issue and its impact
- recommendation: one specific action to address it
- severity: critical | warning | info

Format your response as valid JSON array only, no other text:
[
  {{"title": "...", "summary": "...", "recommendation": "...", "severity": "..."}},
  ...
]"""

    # ── Delay pattern analysis ────────────────────────────
    if use_case == "delay_analysis":
        return f"""{SYSTEM_BASE}
{ctx}
Analyse delivery and payment delay patterns in this dataset.
Focus on: which customers are delayed, what stages are bottlenecks,
and what the financial impact of delays is.
Be specific with numbers."""

    # ── Customer risk assessment ──────────────────────────
    if use_case == "customer_risk":
        cust_json = json.dumps(context.get("customer", {}), indent=2, default=str)
        return f"""{SYSTEM_BASE}
{ctx}
Assess the risk profile of this customer based on their O2C behaviour:
{cust_json}

Provide: risk summary (2 sentences), top 2 risk factors, 2 mitigation actions."""

    # Fallback
    return f"""{SYSTEM_BASE}
{ctx}
{context.get('question', 'Provide a summary of the O2C dataset.')}"""
