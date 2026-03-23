# Unified Data Model

## Primary table: `unified_o2c.csv`
Grain: one row per (sales_order_id, sales_order_item)

## Aggregated: `unified_o2c_orders.csv`
Grain: one row per sales_order_id

## KPI outputs
- `kpi_summary.json`   — top-level metrics
- `customer_kpis.json` — per-customer breakdown

## Key join chain
Sales Order → Delivery (via referenceSdDocument) → Billing (via referenceSdDocument) → Payment (via accountingDocument)
