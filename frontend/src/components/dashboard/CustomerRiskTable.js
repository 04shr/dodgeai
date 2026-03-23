// ── Customer Risk Table ────────────────────────────────
// TODO: render sortable risk-ranked table from customer_kpis.json
import { stageBadge, severityBadge } from "../shared/Badge.js";
import { fmt } from "../../utils/formatters.js";

export function renderCustomerRiskTable(container, customers) {
  const card = document.createElement("div");
  card.className = "card";
  card.style.gridColumn = "span 2";
  card.innerHTML = `
    <div class="card-title">Customer risk ranking</div>
    <table class="data-table">
      <thead><tr>
        <th>Customer</th><th>Revenue</th><th>Cancellations</th>
        <th>Unpaid</th><th>Avg O2C</th><th>Risk</th>
      </tr></thead>
      <tbody id="risk-tbody"></tbody>
    </table>
  `;
  container.appendChild(card);

  const tbody = card.querySelector("#risk-tbody");
  customers.forEach(c => {
    const tr = document.createElement("tr");
    tr.onclick = () => location.hash = `#/customers?id=${c.customer_id}`;
    tr.innerHTML = `
      <td><div style="font-weight:500">${c.customer_name ?? c.customer_id}</div>
          <div style="font-size:11px;color:var(--text-muted)">${c.customer_id}</div></td>
      <td>${fmt.currency(c.total_revenue_inr)}</td>
      <td>${c.cancelled_orders}</td>
      <td>${c.unpaid_orders}</td>
      <td>${fmt.days(c.avg_o2c_days)}</td>
      <td>${severityBadge(Math.min(c.risk_score, 5))}</td>
    `;
    tbody.appendChild(tr);
  });
}
