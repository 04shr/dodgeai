// ── Order Table — paginated list of all orders ─────────
// TODO: sortable columns, row click → drawer
import { stageBadge } from "../shared/Badge.js";
import { fmt } from "../../utils/formatters.js";

export function renderOrderTable(container, orders, onSelect) {
  const el = document.createElement("div");
  el.className = "card";
  el.style.marginTop = "20px";
  el.innerHTML = `
    <div class="card-title">All orders (${orders.length})</div>
    <table class="data-table">
      <thead><tr>
        <th>Order ID</th><th>Customer</th><th>Items</th>
        <th>Revenue</th><th>Stage</th><th>O2C Days</th>
        <th>Issues</th>
      </tr></thead>
      <tbody id="order-tbody"></tbody>
    </table>
  `;
  container.appendChild(el);

  const tbody = el.querySelector("#order-tbody");
  orders.forEach(o => {
    const tr = document.createElement("tr");
    tr.onclick = () => onSelect(o);
    tr.innerHTML = `
      <td class="text-mono" style="font-size:12px">${o.sales_order_id}</td>
      <td>${o.customer_name ?? o.customer_id}</td>
      <td>${o.total_items}</td>
      <td>${fmt.currency(o.order_total_net_amount)}</td>
      <td>${stageBadge(o.lifecycle_stage)}</td>
      <td>${fmt.days(o.total_o2c_days)}</td>
      <td>${o.max_issue_severity > 0
        ? `<span style="color:var(--danger);font-weight:600">${o.max_issue_severity} flag${o.max_issue_severity > 1 ? "s" : ""}</span>`
        : `<span style="color:var(--text-muted)">—</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}
