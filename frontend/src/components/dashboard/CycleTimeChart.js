// ── Cycle Time Chart — bar breakdown ──────────────────
// TODO: render horizontal stacked bar per stage using Chart.js
// Stages: order→delivery, delivery→billing, billing→payment
export function renderCycleTimeChart(container, cycleTimes) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-title">Average cycle time breakdown (days)</div>
    <canvas id="cycle-chart" height="120"></canvas>
  `;
  container.appendChild(card);
  // TODO: Chart.js bar chart
}
