// ── Stage and severity colour helpers ─────────────────
export const stageColor = (stage) => ({
  ordered:   "var(--stage-ordered)",
  delivered: "var(--stage-delivered)",
  billed:    "var(--stage-billed)",
  paid:      "var(--stage-paid)",
  cancelled: "var(--stage-cancelled)",
}[stage] ?? "var(--text-muted)");

export const severityColor = (score) => {
  if (score >= 4) return "var(--danger)";
  if (score >= 3) return "#f97316";
  if (score >= 2) return "var(--warning)";
  if (score >= 1) return "var(--info)";
  return "var(--text-muted)";
};
