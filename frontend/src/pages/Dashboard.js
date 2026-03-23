// ── Dashboard Page ─────────────────────────────────────
import { setTopbarTitle } from "../components/shared/Topbar.js";
import { renderKPIGrid } from "../components/dashboard/KPIGrid.js";
import { renderStageDistribution } from "../components/dashboard/StageDistribution.js";
import { renderCycleTimeChart } from "../components/dashboard/CycleTimeChart.js";
import { renderCustomerRiskTable } from "../components/dashboard/CustomerRiskTable.js";
import { renderRevenueChart } from "../components/dashboard/RevenueChart.js";
import { spinner } from "../components/shared/Spinner.js";

export async function loadDashboard(container) {
  setTopbarTitle("Dashboard");
  container.innerHTML = spinner("Loading dashboard…");

  // Load processed JSON data directly (no backend needed for static mode)
  const [kpis, customers] = await Promise.all([
    fetch("../../data/processed/kpi_summary.json").then(r => r.json()),
    fetch("../../data/processed/customer_kpis.json").then(r => r.json()),
  ]);

  container.innerHTML = "";

  renderKPIGrid(container, kpis);

  const chartsRow = document.createElement("div");
  chartsRow.className = "grid-2";
  chartsRow.style.marginBottom = "24px";
  renderStageDistribution(chartsRow, kpis.lifecycle_stages);
  renderCycleTimeChart(chartsRow, kpis.cycle_times);
  container.appendChild(chartsRow);

  const bottomRow = document.createElement("div");
  bottomRow.className = "grid-2";
  renderCustomerRiskTable(bottomRow, customers);
  renderRevenueChart(bottomRow, customers);
  container.appendChild(bottomRow);
}
