// ── Severity Badge — pip indicator ────────────────────
export function severityPips(score) {
  const pips = Array.from({ length: 5 }, (_, i) => {
    const s = Math.min(score, 5);
    return `<div class="severity-pip ${i < s ? `filled s${i + 1}` : ""}"></div>`;
  }).join("");
  return `<div class="severity-bar">${pips}</div>`;
}
