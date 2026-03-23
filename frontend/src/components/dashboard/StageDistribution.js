// ── Stage Distribution — donut chart + legend ──────────
// TODO: render using Chart.js doughnut
// Data source: kpis.lifecycle_stages
import { stageColor } from "../../utils/colors.js";

export function renderStageDistribution(container, stages) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-title">Lifecycle distribution</div>
    <canvas id="stage-donut" height="200"></canvas>
    <div id="stage-legend" style="display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;font-size:13px"></div>
  `;
  container.appendChild(card);
  // TODO: initialise Chart.js doughnut on #stage-donut
  // TODO: render colour legend chips in #stage-legend
}
