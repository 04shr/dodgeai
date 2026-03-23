// ── Revenue Chart — ordered vs billed vs paid ──────────
// TODO: grouped bar chart comparing revenue at each stage per customer
export function renderRevenueChart(container, customers) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-title">Revenue funnel — ordered vs billed vs paid</div>
    <canvas id="revenue-chart" height="180"></canvas>
  `;
  container.appendChild(card);
  // TODO: Chart.js bar chart — customers on x-axis, 3 bars each
}
