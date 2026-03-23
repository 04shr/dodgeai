// ── Delay Heatmap — customer × issue type matrix ───────
// TODO: render grid of cells coloured by issue frequency per customer
// Rows: customers, Cols: delayed/cancelled/unpaid/missing
export function renderDelayHeatmap(container, customerKpis) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-title">Issue heatmap — customer × issue type</div>
    <div id="heatmap-grid"></div>
  `;
  container.appendChild(card);
  // TODO: build grid from customerKpis data
}
