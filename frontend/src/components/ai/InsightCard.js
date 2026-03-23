// ── AI Insight Card — generated summary tile ──────────
export function renderInsightCard(container, insight) {
  const el = document.createElement("div");
  el.className = "card";
  el.style.borderLeft = "3px solid var(--accent)";
  el.innerHTML = `
    <div class="card-title">${insight.title ?? "AI Insight"}</div>
    <div style="font-size:14px;line-height:1.65;color:var(--text-secondary)">${insight.summary}</div>
    ${insight.recommendation ? `
      <div style="margin-top:12px;padding:10px 14px;background:var(--bg-elevated);border-radius:var(--radius-sm);font-size:13px">
        <span style="color:var(--accent);font-weight:600">Recommendation → </span>${insight.recommendation}
      </div>` : ""}
  `;
  container.appendChild(el);
}
