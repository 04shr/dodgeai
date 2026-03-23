// ── Empty state ────────────────────────────────────────
export function emptyState({ icon = "📭", title = "No data", message = "" }) {
  return `<div class="empty-state">
    <div class="empty-icon">${icon}</div>
    <div style="font-weight:600;color:var(--text-secondary)">${title}</div>
    ${message ? `<div style="font-size:13px">${message}</div>` : ""}
  </div>`;
}
