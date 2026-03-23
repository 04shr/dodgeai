"""
O2C Intelligence — End-to-End API Test Suite
=============================================
Tests every endpoint across all 5 routers + system endpoints.
Outputs structured JSON results to stdout.

Usage:
    # With backend running on localhost:8000 (default)
    python tests/e2e_test.py

    # Custom host / port
    python tests/e2e_test.py --host http://192.168.1.9 --port 8000

    # Save results to file
    python tests/e2e_test.py > results.json

    # With AI endpoints (requires API keys in .env)
    python tests/e2e_test.py --test-ai

Requires: requests  (pip install requests)
"""

import sys
import json
import time
import argparse
import traceback
from datetime import datetime, timezone
from typing import Any

try:
    import requests
    from requests.exceptions import ConnectionError, Timeout, RequestException
except ImportError:
    print(json.dumps({"fatal": "requests not installed. Run: pip install requests"}))
    sys.exit(1)

# ── CLI args ──────────────────────────────────────────
parser = argparse.ArgumentParser(description="O2C E2E Test Suite")
parser.add_argument("--host",     default="http://localhost", help="Backend host URL")
parser.add_argument("--port",     default=8000, type=int,     help="Backend port")
parser.add_argument("--timeout",  default=15,   type=int,     help="Request timeout seconds")
parser.add_argument("--test-ai",  action="store_true",        help="Include AI endpoints (needs API keys)")
parser.add_argument("--verbose",  action="store_true",        help="Include full response bodies in output")
args = parser.parse_args()

BASE     = f"{args.host.rstrip('/')}:{args.port}"
TIMEOUT  = args.timeout
TEST_AI  = args.test_ai
VERBOSE  = args.verbose

# ── Known-good test IDs from the dataset ─────────────
ORDERS = {
    "paid":      "740539",
    "cancelled": "740509",
    "delivered": "740506",
    "billed":    "740543",
    "ordered":   "740584",
}
CUSTOMERS = {
    "high_risk": "320000083",   # Nelson, Fitzpatrick and Jordan — 72 orders, 48 cancellations
    "medium":    "320000082",   # Nguyen-Davis
    "clean":     "320000107",   # Henderson, Garner and Graves — no issues
}
FAKE_ORDER    = "000000000"
FAKE_CUSTOMER = "999999999"

# ── Result collector ──────────────────────────────────
results = {
    "meta": {
        "run_at":    datetime.now(timezone.utc).isoformat(),
        "base_url":  BASE,
        "timeout_s": TIMEOUT,
        "ai_tested": TEST_AI,
    },
    "summary": {
        "total": 0, "passed": 0, "failed": 0, "skipped": 0,
        "total_ms": 0,
    },
    "groups": {}
}

current_group = None

def group(name: str, description: str = ""):
    global current_group
    current_group = name
    results["groups"][name] = {
        "description": description,
        "tests": [],
        "passed": 0, "failed": 0, "skipped": 0,
    }

def skip(name: str, reason: str):
    t = {"name": name, "status": "skipped", "reason": reason}
    results["groups"][current_group]["tests"].append(t)
    results["groups"][current_group]["skipped"] += 1
    results["summary"]["skipped"] += 1
    results["summary"]["total"]   += 1

def test(
    name:        str,
    method:      str,
    path:        str,
    body:        dict | None = None,
    params:      dict | None = None,
    expect_status: int = 200,
    assertions:  list[dict] | None = None,
):
    """
    Run one HTTP test.

    assertions: list of dicts with keys:
      - field:  dot-separated path into JSON response  e.g. "overview.total_orders"
      - op:     "eq" | "gt" | "gte" | "lt" | "lte" | "in" | "contains" | "exists" | "type"
      - value:  expected value (for "type": "int" | "str" | "list" | "dict" | "bool" | "float")
      - label:  optional human-readable description
    """
    url = BASE + path
    t0  = time.perf_counter()
    entry = {
        "name":          name,
        "method":        method.upper(),
        "url":           url,
        "params":        params,
        "status":        None,
        "expected_status": expect_status,
        "latency_ms":    None,
        "assertions":    [],
        "errors":        [],
        "status_result": None,   # "pass" | "fail"
        "overall":       "fail",
    }
    if VERBOSE:
        entry["response_body"] = None

    try:
        resp = requests.request(
            method.upper(), url,
            json=body, params=params,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"} if body else {},
        )
        ms = round((time.perf_counter() - t0) * 1000)
        entry["status"]     = resp.status_code
        entry["latency_ms"] = ms
        results["summary"]["total_ms"] += ms

        # ── Status check ──────────────────────────────
        status_ok = (resp.status_code == expect_status)
        entry["status_result"] = "pass" if status_ok else "fail"
        if not status_ok:
            entry["errors"].append(
                f"Expected HTTP {expect_status}, got {resp.status_code}"
            )

        # ── Parse JSON ────────────────────────────────
        data = None
        try:
            data = resp.json()
            if VERBOSE:
                entry["response_body"] = data
        except Exception:
            if expect_status == 200:
                entry["errors"].append("Response is not valid JSON")

        # ── Run assertions ────────────────────────────
        for assertion in (assertions or []):
            aentry = {
                "label":  assertion.get("label", assertion.get("field", "?")),
                "field":  assertion.get("field"),
                "op":     assertion.get("op", "eq"),
                "expect": assertion.get("value"),
                "actual": None,
                "result": "fail",
            }
            try:
                # Resolve dot-path in response
                val = data
                if assertion.get("field") and data is not None:
                    for part in assertion["field"].split("."):
                        if isinstance(val, dict):
                            val = val.get(part)
                        elif isinstance(val, list) and part.isdigit():
                            val = val[int(part)]
                        else:
                            val = None
                            break
                aentry["actual"] = val

                op    = assertion.get("op", "eq")
                exp   = assertion.get("value")
                ok    = False

                if op == "eq":       ok = val == exp
                elif op == "gt":     ok = val is not None and val > exp
                elif op == "gte":    ok = val is not None and val >= exp
                elif op == "lt":     ok = val is not None and val < exp
                elif op == "lte":    ok = val is not None and val <= exp
                elif op == "in":     ok = exp in val if val is not None else False
                elif op == "contains": ok = val is not None and exp in str(val)
                elif op == "exists": ok = val is not None
                elif op == "type":
                    type_map = {"int": int, "str": str, "list": list, "dict": dict, "bool": bool, "float": float}
                    ok = isinstance(val, type_map.get(exp, object))
                elif op == "not_empty": ok = bool(val)
                elif op == "ne":     ok = val != exp

                aentry["result"] = "pass" if ok else "fail"
                if not ok:
                    entry["errors"].append(
                        f"Assertion '{aentry['label']}': expected {op}({exp!r}), got {val!r}"
                    )
            except Exception as ae:
                aentry["result"] = "fail"
                aentry["error"]  = str(ae)
                entry["errors"].append(f"Assertion error: {ae}")

            entry["assertions"].append(aentry)

    except ConnectionError:
        ms = round((time.perf_counter() - t0) * 1000)
        entry["latency_ms"] = ms
        entry["errors"].append(f"Connection refused — is the backend running at {BASE}?")
        entry["status"] = None
    except Timeout:
        ms = round((time.perf_counter() - t0) * 1000)
        entry["latency_ms"] = ms
        entry["errors"].append(f"Request timed out after {TIMEOUT}s")
    except RequestException as e:
        entry["errors"].append(f"Request failed: {e}")
    except Exception as e:
        entry["errors"].append(f"Unexpected error: {e}\n{traceback.format_exc()}")

    # ── Overall result ────────────────────────────────
    all_assertions_pass = all(a["result"] == "pass" for a in entry["assertions"])
    entry["overall"] = (
        "pass" if (entry["status_result"] == "pass" and all_assertions_pass and not entry["errors"])
        else "fail"
    )

    grp = results["groups"][current_group]
    grp["tests"].append(entry)
    if entry["overall"] == "pass":
        grp["passed"] += 1
        results["summary"]["passed"] += 1
    else:
        grp["failed"] += 1
        results["summary"]["failed"] += 1
    results["summary"]["total"] += 1

    return entry


# ══════════════════════════════════════════════════════
# TEST DEFINITIONS
# ══════════════════════════════════════════════════════

# ── 1. System / Health ────────────────────────────────
group("system", "Root and health check endpoints")

test("GET /  — root endpoint",
     "GET", "/",
     assertions=[
         {"field": "message",  "op": "exists", "label": "message field present"},
         {"field": "docs",     "op": "exists", "label": "docs link present"},
         {"field": "health",   "op": "exists", "label": "health link present"},
     ])

test("GET /health  — data loaded",
     "GET", "/health",
     assertions=[
         {"field": "status",      "op": "eq",  "value": "ok",   "label": "status=ok"},
         {"field": "data_loaded", "op": "eq",  "value": True,   "label": "data_loaded=True"},
         {"field": "orders",      "op": "gte", "value": 100,    "label": "orders >= 100"},
     ])

test("GET /docs  — Swagger UI reachable",
     "GET", "/docs",
     expect_status=200)

# ── 2. KPI Endpoints ──────────────────────────────────
group("kpis", "KPI summary, customer KPIs, issue counts")

test("GET /api/kpis/summary  — full summary structure",
     "GET", "/api/kpis/summary",
     assertions=[
         {"field": "overview",                            "op": "exists", "label": "overview block present"},
         {"field": "lifecycle_stages",                    "op": "exists", "label": "lifecycle_stages present"},
         {"field": "cycle_times",                         "op": "exists", "label": "cycle_times present"},
         {"field": "issues",                              "op": "exists", "label": "issues block present"},
         {"field": "overview.total_orders",               "op": "eq",     "value": 100,  "label": "total_orders=100"},
         {"field": "overview.unique_customers",           "op": "eq",     "value": 8,    "label": "unique_customers=8"},
         {"field": "overview.total_revenue_inr",          "op": "gt",     "value": 0,    "label": "revenue > 0"},
         {"field": "issues.cancellation_rate_pct",        "op": "eq",     "value": 56.0, "label": "cancellation_rate=56%"},
         {"field": "issues.orders_billing_cancelled",     "op": "eq",     "value": 56,   "label": "cancelled orders=56"},
         {"field": "issues.orders_unpaid",                "op": "eq",     "value": 22,   "label": "unpaid orders=22"},
         {"field": "issues.orders_missing_stage",         "op": "eq",     "value": 17,   "label": "missing stage=17"},
         {"field": "issues.orders_with_delivery_delay",   "op": "eq",     "value": 9,    "label": "delivery delays=9"},
         {"field": "cycle_times.avg_total_o2c_days",      "op": "eq",     "value": 6.84, "label": "avg O2C=6.84d"},
         {"field": "lifecycle_stages.cancelled",          "op": "eq",     "value": 56,   "label": "lifecycle cancelled=56"},
     ])

test("GET /api/kpis/summary?stage=cancelled  — filtered KPIs",
     "GET", "/api/kpis/summary",
     params={"stage": "cancelled"},
     assertions=[
         {"field": "overview.total_orders", "op": "eq", "value": 56, "label": "filtered to 56 cancelled"},
         {"field": "filters",               "op": "exists",           "label": "filters block present"},
     ])

test("GET /api/kpis/summary?customer=320000083  — customer filter",
     "GET", "/api/kpis/summary",
     params={"customer": "320000083"},
     assertions=[
         {"field": "overview.total_orders", "op": "eq", "value": 72, "label": "Nelson=72 orders"},
     ])

test("GET /api/kpis/customers  — all 8 customers",
     "GET", "/api/kpis/customers",
     assertions=[
         {"field": None, "op": "type",      "value": "list",    "label": "returns list"},
         {"field": "0",  "op": "exists",                        "label": "at least one customer"},
         {"field": "0.customer_id",   "op": "exists",           "label": "customer_id field"},
         {"field": "0.total_orders",  "op": "gt",   "value": 0, "label": "has orders"},
         {"field": "0.risk_score",    "op": "gt",   "value": 0, "label": "risk_score > 0 (sorted by risk)"},
     ])

test("GET /api/kpis/issues/summary  — issue counts by type",
     "GET", "/api/kpis/issues/summary",
     assertions=[
         {"field": "total_flagged",          "op": "gt",  "value": 0,  "label": "flagged > 0"},
         {"field": "by_type.cancelled",      "op": "eq",  "value": 56, "label": "cancelled=56"},
         {"field": "by_type.unpaid",         "op": "eq",  "value": 22, "label": "unpaid=22"},
         {"field": "by_type.missing",        "op": "eq",  "value": 17, "label": "missing=17"},
         {"field": "by_type.delayed",        "op": "eq",  "value": 9,  "label": "delayed=9"},
         {"field": "by_severity",            "op": "exists",            "label": "by_severity breakdown"},
     ])

# ── 3. Orders Endpoints ───────────────────────────────
group("orders", "Order listing, filtering, single order, items")

test("GET /api/orders  — list all orders",
     "GET", "/api/orders/",
     assertions=[
         {"field": "total",          "op": "eq",   "value": 100,  "label": "total=100"},
         {"field": "data",           "op": "type",  "value": "list","label": "data is list"},
         {"field": "data.0.sales_order_id",   "op": "exists",     "label": "sales_order_id present"},
         {"field": "data.0.lifecycle_stage",  "op": "exists",     "label": "lifecycle_stage present"},
         {"field": "data.0.is_billing_cancelled", "op": "type", "value": "bool", "label": "bool fields parsed"},
     ])

test("GET /api/orders?stage=cancelled  — filter by stage",
     "GET", "/api/orders/",
     params={"stage": "cancelled"},
     assertions=[
         {"field": "total", "op": "eq", "value": 56, "label": "56 cancelled orders"},
     ])

test("GET /api/orders?stage=paid  — filter paid stage",
     "GET", "/api/orders/",
     params={"stage": "paid"},
     assertions=[
         {"field": "total",               "op": "gt",  "value": 0,        "label": "some paid orders"},
         {"field": "data.0.lifecycle_stage","op": "eq", "value": "paid",   "label": "all results are paid"},
     ])

test("GET /api/orders?issue_type=cancelled  — issue type filter",
     "GET", "/api/orders/",
     params={"issue_type": "cancelled"},
     assertions=[
         {"field": "total", "op": "eq", "value": 56, "label": "56 cancelled billing orders"},
     ])

test("GET /api/orders?issue_type=unpaid  — unpaid filter",
     "GET", "/api/orders/",
     params={"issue_type": "unpaid"},
     assertions=[
         {"field": "total", "op": "eq", "value": 22, "label": "22 unpaid orders"},
     ])

test("GET /api/orders?issue_type=missing  — missing stage filter",
     "GET", "/api/orders/",
     params={"issue_type": "missing"},
     assertions=[
         {"field": "total", "op": "eq", "value": 17, "label": "17 missing-stage orders"},
     ])

test("GET /api/orders?issue_type=delayed  — delayed filter",
     "GET", "/api/orders/",
     params={"issue_type": "delayed"},
     assertions=[
         {"field": "total", "op": "eq", "value": 9, "label": "9 delayed orders"},
     ])

test("GET /api/orders?customer=320000083  — customer filter",
     "GET", "/api/orders/",
     params={"customer": "320000083"},
     assertions=[
         {"field": "total", "op": "eq", "value": 72, "label": "72 orders for top customer"},
     ])

test("GET /api/orders?limit=10&offset=0  — pagination page 1",
     "GET", "/api/orders/",
     params={"limit": 10, "offset": 0},
     assertions=[
         {"field": "total",      "op": "eq", "value": 100, "label": "total still 100"},
         {"field": "limit",      "op": "eq", "value": 10,  "label": "limit=10"},
         {"field": "offset",     "op": "eq", "value": 0,   "label": "offset=0"},
     ])

test("GET /api/orders?limit=10&offset=10  — pagination page 2 non-overlapping",
     "GET", "/api/orders/",
     params={"limit": 10, "offset": 10},
     assertions=[
         {"field": "offset", "op": "eq", "value": 10, "label": "offset=10"},
     ])

test(f"GET /api/orders/{ORDERS['paid']}  — single paid order",
     "GET", f"/api/orders/{ORDERS['paid']}",
     assertions=[
         {"field": "sales_order_id",   "op": "exists",              "label": "order found"},
         {"field": "lifecycle_stage",  "op": "eq",  "value": "paid","label": "stage=paid"},
         {"field": "is_billing_cancelled", "op": "eq", "value": False, "label": "not cancelled"},
     ])

test(f"GET /api/orders/{ORDERS['cancelled']}  — single cancelled order",
     "GET", f"/api/orders/{ORDERS['cancelled']}",
     assertions=[
         {"field": "lifecycle_stage",      "op": "eq", "value": "cancelled", "label": "stage=cancelled"},
         {"field": "is_billing_cancelled", "op": "eq", "value": True,        "label": "is_billing_cancelled=True"},
     ])

test(f"GET /api/orders/{ORDERS['ordered']}  — missing stage order",
     "GET", f"/api/orders/{ORDERS['ordered']}",
     assertions=[
         {"field": "lifecycle_stage", "op": "eq",   "value": "ordered", "label": "stage=ordered"},
         {"field": "missing_stage",   "op": "eq",   "value": True,       "label": "missing_stage=True"},
     ])

test(f"GET /api/orders/{FAKE_ORDER}  — 404 for unknown order",
     "GET", f"/api/orders/{FAKE_ORDER}",
     expect_status=404,
     assertions=[
         {"field": "detail", "op": "exists", "label": "detail message present"},
     ])

test(f"GET /api/orders/{ORDERS['paid']}/items  — order items",
     "GET", f"/api/orders/{ORDERS['paid']}/items",
     assertions=[
         {"field": "order_id",    "op": "exists",            "label": "order_id present"},
         {"field": "count",       "op": "gte",  "value": 1,  "label": "at least 1 item"},
         {"field": "items",       "op": "type", "value": "list", "label": "items is list"},
         {"field": "items.0.sales_order_id", "op": "exists", "label": "item has order ref"},
         {"field": "items.0.material_id",    "op": "exists", "label": "material_id present"},
         {"field": "items.0.lifecycle_stage","op": "exists", "label": "lifecycle_stage on item"},
     ])

test(f"GET /api/orders/{FAKE_ORDER}/items  — 404 items for unknown order",
     "GET", f"/api/orders/{FAKE_ORDER}/items",
     expect_status=404)

# ── 4. Issues Endpoints ───────────────────────────────
group("issues", "Issue listing, filtering, annotations, summary")

test("GET /api/issues  — all flagged orders",
     "GET", "/api/issues/",
     assertions=[
         {"field": "total",               "op": "gt",   "value": 0,      "label": "flagged orders exist"},
         {"field": "data.0.issue_labels", "op": "exists",                "label": "issue_labels annotated"},
         {"field": "data.0.issue_labels", "op": "type", "value": "list", "label": "issue_labels is list"},
     ])

test("GET /api/issues?issue_type=cancelled  — cancelled billing filter",
     "GET", "/api/issues/",
     params={"issue_type": "cancelled"},
     assertions=[
         {"field": "total",               "op": "eq", "value": 56, "label": "56 cancelled"},
         {"field": "issue_type_filter",   "op": "eq", "value": "cancelled", "label": "filter reflected"},
     ])

test("GET /api/issues?issue_type=unpaid  — unpaid filter",
     "GET", "/api/issues/",
     params={"issue_type": "unpaid"},
     assertions=[
         {"field": "total", "op": "eq", "value": 22, "label": "22 unpaid"},
     ])

test("GET /api/issues?issue_type=delayed  — delayed filter",
     "GET", "/api/issues/",
     params={"issue_type": "delayed"},
     assertions=[
         {"field": "total", "op": "eq", "value": 9, "label": "9 delayed"},
     ])

test("GET /api/issues?issue_type=missing  — missing stage filter",
     "GET", "/api/issues/",
     params={"issue_type": "missing"},
     assertions=[
         {"field": "total", "op": "eq", "value": 17, "label": "17 missing"},
     ])

test(f"GET /api/issues?customer={CUSTOMERS['high_risk']}  — customer-scoped issues",
     "GET", "/api/issues/",
     params={"customer": CUSTOMERS["high_risk"]},
     assertions=[
         {"field": "total", "op": "gt", "value": 0, "label": "high-risk customer has issues"},
     ])

test("GET /api/issues?min_severity=2  — severity filter",
     "GET", "/api/issues/",
     params={"min_severity": 2},
     assertions=[
         {"field": "total", "op": "gt", "value": 0, "label": "some orders with severity >= 2"},
     ])

test("GET /api/issues/summary  — issue summary counts",
     "GET", "/api/issues/summary",
     assertions=[
         {"field": "total_flagged",     "op": "gt",  "value": 0,  "label": "flagged > 0"},
         {"field": "by_type.cancelled", "op": "eq",  "value": 56, "label": "cancelled=56"},
         {"field": "by_type.unpaid",    "op": "eq",  "value": 22, "label": "unpaid=22"},
         {"field": "by_type.missing",   "op": "eq",  "value": 17, "label": "missing=17"},
         {"field": "by_type.delayed",   "op": "eq",  "value": 9,  "label": "delayed=9"},
         {"field": "by_severity",       "op": "exists",            "label": "by_severity present"},
     ])

# ── 5. Customers Endpoints ────────────────────────────
group("customers", "Customer listing, individual profiles, order history")

test("GET /api/customers  — all customers",
     "GET", "/api/customers/",
     assertions=[
         {"field": None,             "op": "type",  "value": "list",   "label": "returns list"},
         {"field": "0.customer_id",  "op": "exists",                   "label": "customer_id present"},
         {"field": "0.customer_name","op": "exists",                   "label": "customer_name present"},
         {"field": "0.total_orders", "op": "gt",    "value": 0,        "label": "has orders"},
         {"field": "0.risk_score",   "op": "gt",    "value": 0,        "label": "risk score > 0 (sorted)"},
     ])

test(f"GET /api/customers/{CUSTOMERS['high_risk']}  — high risk customer",
     "GET", f"/api/customers/{CUSTOMERS['high_risk']}",
     assertions=[
         {"field": "customer_id",        "op": "exists",               "label": "found"},
         {"field": "customer_name",      "op": "contains", "value": "Nelson", "label": "correct customer"},
         {"field": "total_orders",       "op": "eq",  "value": 72,    "label": "72 orders"},
         {"field": "cancelled_orders",   "op": "eq",  "value": 48,    "label": "48 cancelled"},
         {"field": "risk_score",         "op": "gt",  "value": 0,     "label": "risk score > 0"},
     ])

test(f"GET /api/customers/{CUSTOMERS['clean']}  — clean customer",
     "GET", f"/api/customers/{CUSTOMERS['clean']}",
     assertions=[
         {"field": "customer_id",      "op": "exists",           "label": "found"},
         {"field": "cancelled_orders", "op": "eq", "value": 0,   "label": "no cancellations"},
         {"field": "delayed_orders",   "op": "eq", "value": 0,   "label": "no delays"},
     ])

test(f"GET /api/customers/{FAKE_CUSTOMER}  — 404 for unknown customer",
     "GET", f"/api/customers/{FAKE_CUSTOMER}",
     expect_status=404,
     assertions=[
         {"field": "detail", "op": "exists", "label": "detail message present"},
     ])

test(f"GET /api/customers/{CUSTOMERS['high_risk']}/orders  — customer order history",
     "GET", f"/api/customers/{CUSTOMERS['high_risk']}/orders",
     assertions=[
         {"field": "customer_id",  "op": "eq",   "value": CUSTOMERS["high_risk"], "label": "correct customer"},
         {"field": "count",        "op": "eq",   "value": 72,   "label": "72 orders"},
         {"field": "orders",       "op": "type", "value": "list","label": "orders is list"},
     ])

test(f"GET /api/customers/{FAKE_CUSTOMER}/orders  — 404 for unknown customer orders",
     "GET", f"/api/customers/{FAKE_CUSTOMER}/orders",
     expect_status=404)

# ── 6. AI Endpoints ───────────────────────────────────
group("ai", "NL query, root cause analysis, insights, history, customer risk")

# These tests check endpoint availability and response structure.
# Actual LLM responses are not asserted (depends on API keys).
# Run with --test-ai to include real LLM calls.

if TEST_AI:
    test("POST /api/ai/query  — natural language question",
         "POST", "/api/ai/query",
         body={"question": "What is the cancellation rate?"},
         assertions=[
             {"field": "answer",     "op": "exists",                   "label": "answer present"},
             {"field": "model_used", "op": "exists",                   "label": "model_used present"},
             {"field": "cached",     "op": "type",  "value": "bool",   "label": "cached flag is bool"},
             {"field": "answer",     "op": "not_empty",                "label": "answer not empty"},
         ])

    test("POST /api/ai/query  — cache hit on repeat",
         "POST", "/api/ai/query",
         body={"question": "What is the cancellation rate?"},
         assertions=[
             {"field": "cached", "op": "eq", "value": True, "label": "second call should be cached"},
         ])

    test(f"POST /api/ai/root-cause  — order {ORDERS['cancelled']} (cancelled)",
         "POST", "/api/ai/root-cause",
         body={"order_id": ORDERS["cancelled"]},
         assertions=[
             {"field": "order_id",        "op": "eq",       "value": ORDERS["cancelled"], "label": "order_id echoed"},
             {"field": "analysis",        "op": "not_empty",                               "label": "analysis present"},
             {"field": "recommendations", "op": "type",     "value": "list",              "label": "recommendations is list"},
             {"field": "model_used",      "op": "exists",                                  "label": "model_used present"},
         ])

    test("POST /api/ai/root-cause  — 404 for unknown order",
         "POST", "/api/ai/root-cause",
         body={"order_id": FAKE_ORDER},
         expect_status=404)

    test("GET /api/ai/insights  — system insights",
         "GET", "/api/ai/insights",
         assertions=[
             {"field": "insights",        "op": "type",  "value": "list", "label": "insights is list"},
             {"field": "insights.0.title","op": "exists",                  "label": "first insight has title"},
             {"field": "insights.0.summary","op": "exists",               "label": "first insight has summary"},
         ])

    test(f"POST /api/ai/customer-risk  — high risk customer",
         "POST", "/api/ai/customer-risk",
         body={"customer_id": CUSTOMERS["high_risk"]},
         assertions=[
             {"field": "customer_id", "op": "eq",       "value": CUSTOMERS["high_risk"], "label": "customer_id echoed"},
             {"field": "analysis",    "op": "not_empty",                                  "label": "analysis present"},
             {"field": "model_used",  "op": "exists",                                     "label": "model_used present"},
         ])

    test(f"POST /api/ai/customer-risk  — 404 for unknown customer",
         "POST", "/api/ai/customer-risk",
         body={"customer_id": FAKE_CUSTOMER},
         expect_status=404)

else:
    skip("POST /api/ai/query",           "Skipped — run with --test-ai to include AI endpoints")
    skip("POST /api/ai/query (cached)",  "Skipped — run with --test-ai to include AI endpoints")
    skip("POST /api/ai/root-cause",      "Skipped — run with --test-ai to include AI endpoints")
    skip("POST /api/ai/root-cause 404",  "Skipped — run with --test-ai to include AI endpoints")
    skip("GET /api/ai/insights",         "Skipped — run with --test-ai to include AI endpoints")
    skip("POST /api/ai/customer-risk",   "Skipped — run with --test-ai to include AI endpoints")
    skip("POST /api/ai/customer-risk 404","Skipped — run with --test-ai to include AI endpoints")

test("GET /api/ai/history  — query history (no AI key needed)",
     "GET", "/api/ai/history",
     assertions=[
         {"field": "count",   "op": "type", "value": "int",  "label": "count is int"},
         {"field": "history", "op": "type", "value": "list", "label": "history is list"},
     ])

# ── 7. Edge Cases & Stress ────────────────────────────
group("edge_cases", "Boundary values, invalid inputs, large limits")

test("GET /api/orders?limit=500  — max limit",
     "GET", "/api/orders/",
     params={"limit": 500},
     assertions=[
         {"field": "total", "op": "eq", "value": 100, "label": "total still 100"},
     ])

test("GET /api/orders?stage=nonexistent  — unknown stage returns empty",
     "GET", "/api/orders/",
     params={"stage": "nonexistent"},
     assertions=[
         {"field": "total", "op": "eq", "value": 0, "label": "0 results for bad stage"},
     ])

test("GET /api/orders?sort_by=order_total_net_amount&sort_dir=desc  — sort by amount",
     "GET", "/api/orders/",
     params={"sort_by": "order_total_net_amount", "sort_dir": "desc", "limit": 5},
     assertions=[
         {"field": "data",   "op": "type", "value": "list", "label": "returns list"},
         {"field": "total",  "op": "eq",   "value": 100,    "label": "total unchanged"},
     ])

test("GET /api/orders?limit=1&offset=99  — last page boundary",
     "GET", "/api/orders/",
     params={"limit": 1, "offset": 99},
     assertions=[
         {"field": "offset", "op": "eq", "value": 99,      "label": "offset=99"},
     ])

test("GET /api/kpis/summary?customer=320000083&stage=cancelled  — combined filters",
     "GET", "/api/kpis/summary",
     params={"customer": "320000083", "stage": "cancelled"},
     assertions=[
         {"field": "overview.total_orders", "op": "gt", "value": 0, "label": "filtered results exist"},
     ])

test("GET /api/issues?issue_type=cancelled&customer=320000083  — multi-filter issues",
     "GET", "/api/issues/",
     params={"issue_type": "cancelled", "customer": "320000083"},
     assertions=[
         {"field": "total", "op": "gt", "value": 0, "label": "has cancelled for this customer"},
     ])

test("POST /api/ai/query  — empty question validation",
     "POST", "/api/ai/query",
     body={"question": ""},
     expect_status=422,    # FastAPI validation error
     assertions=[
         {"field": "detail", "op": "exists", "label": "validation detail present"},
     ])

test("POST /api/ai/root-cause  — missing body validation",
     "POST", "/api/ai/root-cause",
     body={},
     expect_status=422)

# ── 8. Response Time Checks ───────────────────────────
group("performance", "Latency checks — all should respond under threshold")

LATENCY_THRESHOLD_MS = 2000  # 2 seconds

perf_tests = [
    ("GET /health",              "GET",  "/health",           None, None),
    ("GET /api/kpis/summary",    "GET",  "/api/kpis/summary", None, None),
    ("GET /api/orders (100)",    "GET",  "/api/orders/",      None, {"limit": 100}),
    ("GET /api/issues",          "GET",  "/api/issues/",      None, None),
    ("GET /api/customers",       "GET",  "/api/customers/",   None, None),
]

for name, method, path, body, params in perf_tests:
    e = test(f"Latency: {name}",
             method, path, body=body, params=params,
             assertions=[])
    # Add latency assertion post-hoc
    if e["latency_ms"] is not None:
        lat_ok = e["latency_ms"] < LATENCY_THRESHOLD_MS
        e["assertions"].append({
            "label":  f"latency < {LATENCY_THRESHOLD_MS}ms",
            "actual": e["latency_ms"],
            "expect": LATENCY_THRESHOLD_MS,
            "op":     "lt",
            "result": "pass" if lat_ok else "fail",
        })
        if not lat_ok:
            e["errors"].append(f"Slow: {e['latency_ms']}ms > {LATENCY_THRESHOLD_MS}ms threshold")
            e["overall"] = "fail"
            results["groups"]["performance"]["passed"] -= 1
            results["groups"]["performance"]["failed"] += 1
            results["summary"]["passed"] -= 1
            results["summary"]["failed"] += 1

# ══════════════════════════════════════════════════════
# FINALISE + OUTPUT
# ══════════════════════════════════════════════════════

# Group-level pass rates
for gname, g in results["groups"].items():
    total_g = g["passed"] + g["failed"] + g["skipped"]
    g["pass_rate"] = round(g["passed"] / max(total_g - g["skipped"], 1) * 100, 1)

# Summary
s = results["summary"]
s["pass_rate"]    = round(s["passed"] / max(s["total"] - s["skipped"], 1) * 100, 1)
s["avg_latency_ms"] = round(s["total_ms"] / max(s["total"] - s["skipped"], 1))

print(json.dumps(results, indent=2, default=str))