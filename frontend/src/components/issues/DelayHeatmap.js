
export function renderDelayHeatmap(container, customerKpis) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-title">Issue heatmap — customer × issue type</div>
    <div id="heatmap-grid"></div>
  `;
  container.appendChild(card);
}
