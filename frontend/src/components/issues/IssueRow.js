// ── Issue Row — single row rendering helper ────────────
// Used internally by IssuePanel; exported for reuse
export function issueRow(order, flags) {
  return `
    <div style="padding:12px 0;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
      <div>
        <span class="text-mono" style="font-size:12px;color:var(--text-muted)">${order.sales_order_id}</span>
        <span style="margin-left:8px;font-weight:500">${order.customer_name ?? order.customer_id}</span>
      </div>
      <div style="display:flex;gap:6px">${flags.map(f => `<span class="badge badge-warning">${f}</span>`).join("")}</div>
    </div>
  `;
}
