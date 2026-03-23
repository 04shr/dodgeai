// ── Spinner — loading indicator ────────────────────────
export function spinner(msg = "Loading…") {
  return `<div style="display:flex;align-items:center;gap:12px;padding:48px;justify-content:center;color:var(--text-muted)">
    <div class="spinner"></div><span>${msg}</span>
  </div>`;
}
