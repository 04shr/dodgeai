// ── Badge — lifecycle stage / severity pill ────────────
export function stageBadge(stage) {
  return `<span class="badge badge-${stage}">${stage.charAt(0).toUpperCase() + stage.slice(1)}</span>`;
}

export function severityBadge(score) {
  const level = score >= 4 ? "critical" : score >= 2 ? "warning" : "info";
  const label = score >= 4 ? "Critical" : score >= 2 ? "Warning" : "Low";
  return `<span class="badge badge-${level}">${label}</span>`;
}
