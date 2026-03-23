// ── KPI Grid — 4-up metric tiles ──────────────────────
// TODO: fetch from api.getKpiSummary() and render renderKPICard tiles
// Slots: Total Revenue, Cancellation Rate, Avg O2C Days, Revenue Leakage
import { renderKPICard } from "../shared/KPICard.js";
import { fmt } from "../../utils/formatters.js";

export function renderKPIGrid(container, kpis) {
  const grid = document.createElement("div");
  grid.className = "grid-4";
  grid.style.marginBottom = "24px";

  const o = kpis.overview;
  const i = kpis.issues;
  const c = kpis.cycle_times;

  const tiles = [
    { label: "Total Revenue",      value: fmt.currency(o.total_revenue_inr),       sub: `${fmt.currency(o.total_paid_inr)} collected`, accent: "var(--accent)" },
    { label: "Cancellation Rate",  value: fmt.pct(i.cancellation_rate_pct),         sub: `${i.orders_billing_cancelled} orders cancelled`, delta: "High", deltaDir: "down", accent: "var(--danger)" },
    { label: "Avg O2C Cycle",      value: fmt.days(c.avg_total_o2c_days),           sub: `Median ${fmt.days(c.median_total_o2c_days)}`, accent: "var(--warning)" },
    { label: "Revenue Leakage",    value: fmt.currency(o.revenue_leakage_inr),      sub: `${fmt.pct(100 - o.payment_coverage_pct)} uncollected`, accent: "var(--stage-billed)" },
    { label: "Orders Unpaid",      value: i.orders_unpaid,                          sub: "Billed, awaiting payment", accent: "var(--info)" },
    { label: "Delivery Delays",    value: i.orders_with_delivery_delay,             sub: `${fmt.pct(i.delivery_delay_rate_pct)} of orders`, accent: "var(--warning)" },
    { label: "Billing Coverage",   value: fmt.pct(o.billing_coverage_pct),          sub: "Of total order value", accent: "var(--success)" },
    { label: "Missing Stages",     value: i.orders_missing_stage,                   sub: "Orders without full lifecycle", accent: "var(--stage-cancelled)" },
  ];

  tiles.forEach(t => grid.appendChild(renderKPICard(t)));
  container.appendChild(grid);
}
