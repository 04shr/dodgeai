// ── Issue Panel — full flagged orders list ─────────────
// TODO: filter by issue type, severity; click row → OrderDetailDrawer
import { severityBadge, stageBadge } from "../shared/Badge.js";
import { fmt } from "../../utils/formatters.js";
import { openOrderDrawer } from "../lifecycle/OrderDetailDrawer.js";

export function renderIssuePanel(container, orders) {
  const flagged = orders.filter(o => o.max_issue_severity > 0 || o.is_billing_cancelled === "True");

  const el = document.createElement("div");
  el.className = "card";
  el.innerHTML = `
    <div class="card-title">Flagged orders — ${flagged.length} issues detected</div>
    <table class="data-table">
      <thead><tr>
        <th>Order</th><th>Customer</th><th>Stage</th>
        <th>Flags</th><th>Severity</th><th>Revenue</th>
      </tr></thead>
      <tbody id="issue-tbody"></tbody>
    </table>
  `;
  container.appendChild(el);

  const tbody = el.querySelector("#issue-tbody");
  flagged.forEach(o => {
    const flags = [
      o.is_delivery_delayed === "True"   && "Delayed delivery",
      o.is_payment_overdue  === "True"   && "Payment overdue",
      o.is_billing_cancelled === "True"  && "Billing cancelled",
      o.is_unpaid           === "True"   && "Unpaid",
      o.missing_stage       === "True"   && "Missing stage",
    ].filter(Boolean);

    const tr = document.createElement("tr");
    tr.onclick = () => openOrderDrawer(o);
    tr.innerHTML = `
      <td class="text-mono" style="font-size:12px">${o.sales_order_id}</td>
      <td>${o.customer_name ?? o.customer_id}</td>
      <td>${stageBadge(o.lifecycle_stage)}</td>
      <td><div style="display:flex;flex-wrap:wrap;gap:4px">${flags.map(f => `<span class="badge badge-warning">${f}</span>`).join("")}</div></td>
      <td>${severityBadge(Number(o.max_issue_severity))}</td>
      <td>${fmt.currency(o.order_total_net_amount)}</td>
    `;
    tbody.appendChild(tr);
  });
}
