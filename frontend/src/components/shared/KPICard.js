// ── KPI Card — renders a single metric tile ────────────
export function renderKPICard({ label, value, sub, delta, deltaDir, accent }) {
  const el = document.createElement("div");
  el.className = "kpi-card";
  if (accent) el.style.borderTop = `2px solid ${accent}`;
  el.innerHTML = `
    <div class="kpi-label">${label}</div>
    <div class="kpi-value">${value}</div>
    ${sub    ? `<div class="kpi-sub">${sub}</div>` : ""}
    ${delta  ? `<div class="kpi-delta ${deltaDir ?? ""}">${delta}</div>` : ""}
  `;
  return el;
}
