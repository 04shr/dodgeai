// ── Issues Page ────────────────────────────────────────
import { setTopbarTitle } from "../components/shared/Topbar.js";
import { renderIssuePanel } from "../components/issues/IssuePanel.js";
import { renderDelayHeatmap } from "../components/issues/DelayHeatmap.js";
import { spinner } from "../components/shared/Spinner.js";

export async function loadIssues(container) {
  setTopbarTitle("Issue Monitor");
  container.innerHTML = spinner("Loading issues…");

  const [orders, customers] = await Promise.all([
    fetch("../../data/processed/unified_o2c_orders.csv").then(r => r.text()).then(csvToObjects),
    fetch("../../data/processed/customer_kpis.json").then(r => r.json()),
  ]);

  container.innerHTML = "";

  // Summary chips
  const flagged = orders.filter(o => o.max_issue_severity > 0 || o.is_billing_cancelled === "True");
  container.innerHTML = `
    <div style="display:flex;gap:12px;margin-bottom:22px;flex-wrap:wrap">
      <div class="kpi-card" style="flex:1;min-width:160px;border-top:2px solid var(--danger)">
        <div class="kpi-label">Cancellations</div>
        <div class="kpi-value">${orders.filter(o => o.lifecycle_stage === "cancelled").length}</div>
      </div>
      <div class="kpi-card" style="flex:1;min-width:160px;border-top:2px solid var(--warning)">
        <div class="kpi-label">Delivery Delays</div>
        <div class="kpi-value">${orders.filter(o => o.is_delivery_delayed === "True").length}</div>
      </div>
      <div class="kpi-card" style="flex:1;min-width:160px;border-top:2px solid var(--info)">
        <div class="kpi-label">Unpaid Orders</div>
        <div class="kpi-value">${orders.filter(o => o.is_unpaid === "True").length}</div>
      </div>
      <div class="kpi-card" style="flex:1;min-width:160px;border-top:2px solid var(--stage-delivered)">
        <div class="kpi-label">Missing Stages</div>
        <div class="kpi-value">${orders.filter(o => o.missing_stage === "True").length}</div>
      </div>
    </div>`;

  const grid = document.createElement("div");
  grid.className = "grid-2";
  renderIssuePanel(grid, orders);
  renderDelayHeatmap(grid, customers);
  container.appendChild(grid);
}

function csvToObjects(csv) {
  const [headerLine, ...rows] = csv.trim().split("\n");
  const headers = headerLine.split(",");
  return rows.map(row => {
    const vals = row.split(",");
    return Object.fromEntries(headers.map((h, i) => [h, vals[i] ?? ""]));
  });
}
