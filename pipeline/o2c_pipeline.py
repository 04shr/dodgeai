"""
O2C Intelligence System — Unified Data Pipeline
================================================
Loads all SAP JSONL tables, joins them into a single analytical table,
computes KPIs and cycle times, and flags operational issues.

Output:
  - unified_o2c.csv           → full grain (one row per order item)
  - unified_o2c_orders.csv    → order-level aggregated view
  - kpi_summary.json          → top-level business KPIs
  - customer_kpis.json        → per-customer breakdowns
"""

import json
import glob
import os
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

DATA_ROOT = Path("../data/raw/sap-o2c-data")
OUT_DIR   = Path("../data/processed")  # where output should go
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Delay thresholds (days)
DELIVERY_DELAY_THRESHOLD = 3   # > 3 days from order to delivery = delayed
PAYMENT_OVERDUE_THRESHOLD = 30  # > 30 days from billing to payment = overdue

# Payment term to expected days map (SAP codes found in data)
PAYMENT_TERM_DAYS = {
    "Z001": 30,   # Net 30
    "Z009": 0,    # Immediate / pay on delivery
}
DEFAULT_PAYMENT_DAYS = 30


# ─────────────────────────────────────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_jsonl(folder: str) -> pd.DataFrame:
    """Load all JSONL part-files in a folder into a single DataFrame."""
    rows = []
    pattern = DATA_ROOT / folder / "*.jsonl"
    files = glob.glob(str(pattern))
    if not files:
        print(f"  [WARN] No files found: {pattern}")
        return pd.DataFrame()
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    df = pd.DataFrame(rows)
    print(f"  Loaded {folder:45s} → {len(df):>5} rows, {len(df.columns)} cols")
    return df


def parse_date_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Parse ISO date strings to timezone-naive datetime64."""
    if col not in df.columns:
        return pd.NaT
    return pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_localize(None)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — LOAD ALL TABLES
# ─────────────────────────────────────────────────────────────────────────────

def load_all_tables() -> dict:
    print("\n[1] Loading source tables...")
    tables = {
        "so_headers":  load_jsonl("sales_order_headers"),
        "so_items":    load_jsonl("sales_order_items"),
        "od_headers":  load_jsonl("outbound_delivery_headers"),
        "od_items":    load_jsonl("outbound_delivery_items"),
        "bd_headers":  load_jsonl("billing_document_headers"),
        "bd_items":    load_jsonl("billing_document_items"),
        "payments":    load_jsonl("payments_accounts_receivable"),
        "partners":    load_jsonl("business_partners"),
        "cancels":     load_jsonl("billing_document_cancellations"),
        "products":    load_jsonl("products"),
        "prod_desc":   load_jsonl("product_descriptions"),
    }
    return tables


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — CLEAN & NORMALISE
# ─────────────────────────────────────────────────────────────────────────────

def clean_tables(t: dict) -> dict:
    print("\n[2] Cleaning & normalising...")

    # ── Sales order headers ──────────────────────────────────────────────────
    soh = t["so_headers"].copy()
    soh["order_created_date"]       = parse_date_col(soh, "creationDate")
    soh["requested_delivery_date"]  = parse_date_col(soh, "requestedDeliveryDate")
    soh["order_total_net_amount"]   = pd.to_numeric(soh["totalNetAmount"], errors="coerce")
    soh = soh.rename(columns={
        "salesOrder":               "sales_order_id",
        "soldToParty":              "customer_id",
        "salesOrderType":           "order_type",
        "salesOrganization":        "sales_org",
        "customerPaymentTerms":     "payment_terms",
        "overallDeliveryStatus":    "overall_delivery_status",
        "deliveryBlockReason":      "delivery_block_reason",
        "headerBillingBlockReason": "billing_block_reason",
        "transactionCurrency":      "currency",
    })
    soh_cols = ["sales_order_id", "customer_id", "order_type", "sales_org",
                "payment_terms", "currency", "order_created_date",
                "requested_delivery_date", "order_total_net_amount",
                "overall_delivery_status", "delivery_block_reason", "billing_block_reason"]
    t["soh"] = soh[soh_cols]

    # ── Sales order items ────────────────────────────────────────────────────
    soi = t["so_items"].copy()
    soi["item_net_amount"] = pd.to_numeric(soi["netAmount"], errors="coerce")
    soi["item_qty"]        = pd.to_numeric(soi["requestedQuantity"], errors="coerce")
    soi = soi.rename(columns={
        "salesOrder":               "sales_order_id",
        "salesOrderItem":           "sales_order_item",
        "material":                 "material_id",
        "materialGroup":            "material_group",
        "requestedQuantityUnit":    "qty_unit",
        "salesDocumentRjcnReason":  "rejection_reason",
        "itemBillingBlockReason":   "item_billing_block",
        "productionPlant":          "plant",
    })
    soi_cols = ["sales_order_id", "sales_order_item", "material_id", "material_group",
                "item_qty", "qty_unit", "item_net_amount", "plant",
                "rejection_reason", "item_billing_block"]
    t["soi"] = soi[soi_cols]

    # ── Delivery headers ─────────────────────────────────────────────────────
    odh = t["od_headers"].copy()
    odh["delivery_created_date"]     = parse_date_col(odh, "creationDate")
    odh["actual_goods_movement_date"] = parse_date_col(odh, "actualGoodsMovementDate")
    odh = odh.rename(columns={
        "deliveryDocument":              "delivery_id",
        "overallGoodsMovementStatus":    "goods_movement_status",
        "overallPickingStatus":          "picking_status",
        "deliveryBlockReason":           "delivery_block",
        "shippingPoint":                 "shipping_point",
    })
    odh_cols = ["delivery_id", "delivery_created_date", "actual_goods_movement_date",
                "goods_movement_status", "picking_status", "delivery_block", "shipping_point"]
    t["odh"] = odh[odh_cols]

    # ── Delivery items (carry the order→delivery link) ───────────────────────
    odi = t["od_items"].copy()
    odi["actual_delivery_qty"] = pd.to_numeric(odi["actualDeliveryQuantity"], errors="coerce")
    odi = odi.rename(columns={
        "deliveryDocument":        "delivery_id",
        "deliveryDocumentItem":    "delivery_item",
        "referenceSdDocument":     "sales_order_id",
        "referenceSdDocumentItem": "sales_order_item",
        "plant":                   "delivery_plant",
        "storageLocation":         "storage_location",
    })
    odi_cols = ["delivery_id", "delivery_item", "sales_order_id", "sales_order_item",
                "actual_delivery_qty", "delivery_plant", "storage_location"]
    t["odi"] = odi[odi_cols]
    # normalise item to plain int string to match sales order item format
    t["odi"]["sales_order_item"] = t["odi"]["sales_order_item"].str.lstrip("0").str.strip()

    # ── Billing headers ──────────────────────────────────────────────────────
    bdh = t["bd_headers"].copy()
    bdh["billing_date"]    = parse_date_col(bdh, "billingDocumentDate")
    bdh["billing_created"] = parse_date_col(bdh, "creationDate")
    bdh["billing_amount"]  = pd.to_numeric(bdh["totalNetAmount"], errors="coerce")
    bdh = bdh.rename(columns={
        "billingDocument":           "billing_doc_id",
        "billingDocumentType":       "billing_type",
        "billingDocumentIsCancelled":"is_cancelled",
        "accountingDocument":        "accounting_document",
        "soldToParty":               "billing_customer_id",
        "companyCode":               "company_code",
    })
    bdh_cols = ["billing_doc_id", "billing_type", "billing_date", "billing_created",
                "billing_amount", "is_cancelled", "accounting_document",
                "billing_customer_id", "company_code"]
    t["bdh"] = bdh[bdh_cols]

    # ── Billing items (carry the delivery→billing link) ──────────────────────
    bdi = t["bd_items"].copy()
    bdi["billed_qty"]    = pd.to_numeric(bdi["billingQuantity"], errors="coerce")
    bdi["billed_amount"] = pd.to_numeric(bdi["netAmount"], errors="coerce")
    bdi = bdi.rename(columns={
        "billingDocument":         "billing_doc_id",
        "billingDocumentItem":     "billing_doc_item",
        "material":                "material_id",
        "referenceSdDocument":     "delivery_id",
        "referenceSdDocumentItem": "delivery_item",
    })
    bdi_cols = ["billing_doc_id", "billing_doc_item", "delivery_id",
                "delivery_item", "material_id", "billed_qty", "billed_amount"]
    t["bdi"] = bdi[bdi_cols]

    # ── Payments ─────────────────────────────────────────────────────────────
    pay = t["payments"].copy()
    pay["posting_date"] = parse_date_col(pay, "postingDate")
    pay["clearing_date"] = parse_date_col(pay, "clearingDate")
    pay["amount_paid"]   = pd.to_numeric(pay["amountInTransactionCurrency"], errors="coerce")
    pay = pay.rename(columns={
        "accountingDocument": "accounting_document",
        "customer":           "paying_customer",
        "transactionCurrency":"pay_currency",
    })
    pay_cols = ["accounting_document", "posting_date", "clearing_date",
                "amount_paid", "pay_currency", "paying_customer"]
    t["pay"] = pay[pay_cols]

    # ── Business partners (customer lookup) ──────────────────────────────────
    bp = t["partners"].copy()
    bp = bp.rename(columns={
        "businessPartner":     "customer_id",
        "businessPartnerFullName": "customer_name",
        "businessPartnerIsBlocked": "is_blocked",
    })
    t["bp"] = bp[["customer_id", "customer_name", "is_blocked"]]

    # ── Product descriptions lookup ──────────────────────────────────────────
    pdesc = t["prod_desc"].copy() if len(t["prod_desc"]) else pd.DataFrame()
    if len(pdesc):
        pdesc = pdesc.rename(columns={
            "product":     "material_id",
            "productDescription": "material_desc",
        })
        if "material_id" in pdesc.columns and "material_desc" in pdesc.columns:
            t["pdesc"] = pdesc[["material_id", "material_desc"]].drop_duplicates("material_id")
        else:
            t["pdesc"] = pd.DataFrame(columns=["material_id", "material_desc"])
    else:
        t["pdesc"] = pd.DataFrame(columns=["material_id", "material_desc"])

    print("  Cleaning done.")
    return t


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — JOIN INTO UNIFIED TABLE
# ─────────────────────────────────────────────────────────────────────────────

def build_unified_table(t: dict) -> pd.DataFrame:
    print("\n[3] Building unified O2C table...")

    # Base: order items × order headers
    base = t["soi"].merge(t["soh"], on="sales_order_id", how="left")
    print(f"  order items × headers      → {len(base)} rows")

    # Attach delivery items (left join: orders with no delivery get NULLs)
    # normalise sales_order_item to strip leading zeros for matching
    base["sales_order_item_norm"] = base["sales_order_item"].astype(str).str.lstrip("0").str.strip()
    odi_norm = t["odi"].copy()
    odi_norm["sales_order_item_norm"] = odi_norm["sales_order_item"].astype(str).str.lstrip("0").str.strip()

    base = base.merge(
        odi_norm[["sales_order_id", "sales_order_item_norm", "delivery_id",
                  "delivery_item", "actual_delivery_qty", "delivery_plant", "storage_location"]],
        on=["sales_order_id", "sales_order_item_norm"],
        how="left"
    )
    print(f"  + delivery items           → {len(base)} rows  (nulls where no delivery)")

    # Attach delivery headers
    base = base.merge(t["odh"], on="delivery_id", how="left")
    print(f"  + delivery headers         → {len(base)} rows")

    # Attach billing items via delivery_id
    bdi_agg = t["bdi"].groupby("delivery_id").agg(
        billing_doc_id    = ("billing_doc_id",  "first"),
        billed_qty        = ("billed_qty",       "sum"),
        billed_amount_sum = ("billed_amount",    "sum"),
    ).reset_index()
    base = base.merge(bdi_agg, on="delivery_id", how="left")
    print(f"  + billing items (agg)      → {len(base)} rows")

    # Attach billing headers
    base = base.merge(t["bdh"], on="billing_doc_id", how="left")
    print(f"  + billing headers          → {len(base)} rows")

    # Attach payments via accounting_document
    pay_agg = t["pay"].groupby("accounting_document").agg(
        payment_posting_date = ("posting_date",  "min"),
        payment_clearing_date = ("clearing_date", "min"),
        total_amount_paid    = ("amount_paid",    "sum"),
    ).reset_index()
    base = base.merge(pay_agg, on="accounting_document", how="left")
    print(f"  + payments                 → {len(base)} rows")

    # Enrich with customer name
    base = base.merge(t["bp"], on="customer_id", how="left")

    # Enrich with product description
    if len(t["pdesc"]):
        base = base.merge(t["pdesc"], on="material_id", how="left")
    else:
        base["material_desc"] = ""

    print(f"  Final unified table        → {len(base)} rows, {len(base.columns)} columns")
    return base


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — COMPUTE KPI COLUMNS
# ─────────────────────────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[4] Computing KPI columns...")

    # ── Cycle time calculations ──────────────────────────────────────────────
    def days_between(col_a, col_b):
        return (col_b - col_a).dt.days

    df["order_to_delivery_days"] = days_between(
        df["order_created_date"], df["delivery_created_date"]
    )
    df["delivery_to_billing_days"] = days_between(
        df["delivery_created_date"], df["billing_date"]
    )
    df["billing_to_payment_days"] = days_between(
        df["billing_date"], df["payment_posting_date"]
    )
    df["total_o2c_days"] = days_between(
        df["order_created_date"], df["payment_posting_date"]
    )

    # ── Lifecycle stage ──────────────────────────────────────────────────────
    def derive_stage(row):
        if row.get("is_cancelled") is True:
            return "cancelled"
        if pd.notna(row.get("payment_posting_date")):
            return "paid"
        if pd.notna(row.get("billing_doc_id")):
            return "billed"
        if pd.notna(row.get("delivery_id")):
            return "delivered"
        return "ordered"

    df["lifecycle_stage"] = df.apply(derive_stage, axis=1)

    # ── Missing stage detection ──────────────────────────────────────────────
    df["has_delivery"] = df["delivery_id"].notna()
    df["has_billing"]  = df["billing_doc_id"].notna()
    df["has_payment"]  = df["payment_posting_date"].notna()
    df["missing_stage"] = ~df["has_delivery"] | (~df["has_billing"] & df["has_delivery"])

    # ── Issue flags ──────────────────────────────────────────────────────────
    # Delivery delay: order → delivery took more than threshold days
    df["is_delivery_delayed"] = (
        df["order_to_delivery_days"].notna() &
        (df["order_to_delivery_days"] > DELIVERY_DELAY_THRESHOLD)
    )

    # Payment overdue: billing → payment exceeded expected payment term
    expected_days = df["payment_terms"].map(PAYMENT_TERM_DAYS).fillna(DEFAULT_PAYMENT_DAYS)
    df["expected_payment_days"] = expected_days
    df["is_payment_overdue"] = (
        df["billing_to_payment_days"].notna() &
        (df["billing_to_payment_days"] > expected_days)
    )

    # Still unpaid (billed but no payment cleared yet)
    df["is_unpaid"] = df["has_billing"] & ~df["has_payment"] & (df["is_cancelled"] != True)

    # Cancelled billing
    df["is_billing_cancelled"] = df["is_cancelled"].fillna(False).astype(bool)

    # Rejection (order item was rejected)
    df["is_rejected"] = df["rejection_reason"].notna() & (df["rejection_reason"] != "")

    # Delivery block
    df["has_delivery_block"] = (
        df["delivery_block_reason"].notna() & (df["delivery_block_reason"] != "")
    )

    # Severity scoring  (simple additive, 0–5)
    df["issue_severity"] = (
        df["is_delivery_delayed"].astype(int) +
        df["is_payment_overdue"].astype(int) +
        df["is_billing_cancelled"].astype(int) +
        df["is_unpaid"].astype(int) +
        df["missing_stage"].astype(int)
    )

    print("  KPI columns added.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — ORDER-LEVEL AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────

def build_order_view(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[5] Building order-level view...")

    agg = df.groupby("sales_order_id").agg(
        customer_id             = ("customer_id",           "first"),
        customer_name           = ("customer_name",         "first"),
        order_created_date      = ("order_created_date",    "first"),
        requested_delivery_date = ("requested_delivery_date","first"),
        payment_terms           = ("payment_terms",         "first"),
        currency                = ("currency",              "first"),
        order_total_net_amount  = ("order_total_net_amount","first"),
        total_items             = ("sales_order_item",      "count"),
        total_billed_amount     = ("billed_amount_sum",     "sum"),
        total_paid_amount       = ("total_amount_paid",     "sum"),
        lifecycle_stage         = ("lifecycle_stage",       lambda x: x.mode()[0] if len(x) else "unknown"),
        order_to_delivery_days  = ("order_to_delivery_days","min"),
        delivery_to_billing_days = ("delivery_to_billing_days","min"),
        billing_to_payment_days = ("billing_to_payment_days","min"),
        total_o2c_days          = ("total_o2c_days",        "min"),
        is_delivery_delayed     = ("is_delivery_delayed",   "any"),
        is_payment_overdue      = ("is_payment_overdue",    "any"),
        is_billing_cancelled    = ("is_billing_cancelled",  "any"),
        is_unpaid               = ("is_unpaid",             "any"),
        missing_stage           = ("missing_stage",         "any"),
        max_issue_severity      = ("issue_severity",        "max"),
    ).reset_index()

    # Revenue leakage: ordered but not billed or billed but not paid
    agg["revenue_leakage_amount"] = agg["order_total_net_amount"] - agg["total_paid_amount"].fillna(0)

    print(f"  Order-level view → {len(agg)} orders")
    return agg


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — SUMMARY KPIs
# ─────────────────────────────────────────────────────────────────────────────

def build_kpi_summary(df_items: pd.DataFrame, df_orders: pd.DataFrame) -> dict:
    print("\n[6] Computing summary KPIs...")

    def safe_mean(s): return round(float(s.dropna().mean()), 2) if len(s.dropna()) > 0 else None
    def safe_median(s): return round(float(s.dropna().median()), 2) if len(s.dropna()) > 0 else None

    total_orders    = len(df_orders)
    total_revenue   = round(float(df_orders["order_total_net_amount"].sum()), 2)
    # Deduplicate before summing — billing/payment docs span multiple order items
    total_billed    = round(float(df_items.drop_duplicates("billing_doc_id")["billing_amount"].dropna().sum()), 2)
    total_paid      = round(float(df_items.drop_duplicates("accounting_document")["total_amount_paid"].dropna().sum()), 2)

    stage_counts = df_orders["lifecycle_stage"].value_counts().to_dict()

    kpis = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overview": {
            "total_orders":             total_orders,
            "total_order_items":        len(df_items),
            "unique_customers":         df_orders["customer_id"].nunique(),
            "total_revenue_inr":        total_revenue,
            "total_billed_inr":         total_billed,
            "total_paid_inr":           total_paid,
            "revenue_leakage_inr":      round(total_revenue - total_paid, 2),
            "billing_coverage_pct":     round(total_billed / total_revenue * 100, 1) if total_revenue else 0,
            "payment_coverage_pct":     round(total_paid / total_revenue * 100, 1) if total_revenue else 0,
        },
        "lifecycle_stages": stage_counts,
        "cycle_times": {
            "avg_order_to_delivery_days":   safe_mean(df_orders["order_to_delivery_days"]),
            "median_order_to_delivery_days": safe_median(df_orders["order_to_delivery_days"]),
            "avg_delivery_to_billing_days": safe_mean(df_orders["delivery_to_billing_days"]),
            "avg_billing_to_payment_days":  safe_mean(df_orders["billing_to_payment_days"]),
            "avg_total_o2c_days":           safe_mean(df_orders["total_o2c_days"]),
            "median_total_o2c_days":        safe_median(df_orders["total_o2c_days"]),
        },
        "issues": {
            "orders_with_delivery_delay":   int(df_orders["is_delivery_delayed"].sum()),
            "orders_payment_overdue":       int(df_orders["is_payment_overdue"].sum()),
            "orders_billing_cancelled":     int(df_orders["is_billing_cancelled"].sum()),
            "orders_unpaid":                int(df_orders["is_unpaid"].sum()),
            "orders_missing_stage":         int(df_orders["missing_stage"].sum()),
            "cancellation_rate_pct":        round(df_orders["is_billing_cancelled"].mean() * 100, 1),
            "delivery_delay_rate_pct":      round(df_orders["is_delivery_delayed"].mean() * 100, 1),
        },
    }
    return kpis


def build_customer_kpis(df_orders: pd.DataFrame) -> list:
    print("\n[7] Computing customer-level KPIs...")
    customers = []
    for cust_id, grp in df_orders.groupby("customer_id"):
        customers.append({
            "customer_id":         cust_id,
            "customer_name":       grp["customer_name"].iloc[0] if "customer_name" in grp else cust_id,
            "total_orders":        len(grp),
            "total_revenue_inr":   round(float(grp["order_total_net_amount"].sum()), 2),
            "total_paid_inr":      round(float(grp["total_paid_amount"].fillna(0).sum()), 2),
            "avg_o2c_days":        round(float(grp["total_o2c_days"].dropna().mean()), 2) if grp["total_o2c_days"].notna().any() else None,
            "cancelled_orders":    int(grp["is_billing_cancelled"].sum()),
            "overdue_orders":      int(grp["is_payment_overdue"].sum()),
            "unpaid_orders":       int(grp["is_unpaid"].sum()),
            "delayed_orders":      int(grp["is_delivery_delayed"].sum()),
            "risk_score":          int(grp["max_issue_severity"].sum()),
        })
    customers.sort(key=lambda x: x["risk_score"], reverse=True)
    return customers


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline():
    print("=" * 60)
    print("  O2C INTELLIGENCE PIPELINE")
    print("=" * 60)

    tables   = load_all_tables()
    tables   = clean_tables(tables)
    unified  = build_unified_table(tables)
    unified  = compute_kpis(unified)
    orders   = build_order_view(unified)
    kpi_sum  = build_kpi_summary(unified, orders)
    cust_kpi = build_customer_kpis(orders)

    # ── Save outputs ──────────────────────────────────────────────────────────
    print("\n[8] Writing outputs...")
    unified.to_csv(OUT_DIR / "unified_o2c.csv", index=False)
    orders.to_csv(OUT_DIR / "unified_o2c_orders.csv", index=False)

    with open(OUT_DIR / "kpi_summary.json", "w") as f:
        json.dump(kpi_sum, f, indent=2, default=str)
    with open(OUT_DIR / "customer_kpis.json", "w") as f:
        json.dump(cust_kpi, f, indent=2, default=str)

    print(f"\n  unified_o2c.csv          → {len(unified)} rows")
    print(f"  unified_o2c_orders.csv   → {len(orders)} rows")
    print(f"  kpi_summary.json         ✓")
    print(f"  customer_kpis.json       ✓")

    print("\n[SUMMARY SNAPSHOT]")
    print(json.dumps(kpi_sum, indent=2, default=str))

    return unified, orders, kpi_sum, cust_kpi


if __name__ == "__main__":
    run_pipeline()
