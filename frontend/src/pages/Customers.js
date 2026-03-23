// ── Customers Page ─────────────────────────────────────
import { setTopbarTitle } from "../components/shared/Topbar.js";
import { fmt } from "../utils/formatters.js";
import { severityBadge } from "../components/shared/Badge.js";
import { spinner } from "../components/shared/Spinner.js";

export async function loadCustomers(container) {
  setTopbarTitle("Customer Profiles");
  container.innerHTML = spinner("Loading customers…");

  const customers = await fetch("../../data/processed/customer_kpis.json").then(r => r.json());

  container.innerHTML = "";

  const grid = document.createElement("div");
  grid.className = "grid-3";

  customers.forEach(c => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.cursor = "pointer";
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">
        <div>
          <div style="font-weight:600;font-size:15px">${c.customer_name ?? c.customer_id}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${c.customer_id}</div>
        </div>
        ${severityBadge(Math.min(Math.floor(c.risk_score / 5), 5))}
      </div>
      <div class="grid-2" style="gap:10px">
        <div><div style="font-size:11px;color:var(--text-muted)">REVENUE</div><div style="font-weight:600">${fmt.currency(c.total_revenue_inr)}</div></div>
        <div><div style="font-size:11px;color:var(--text-muted)">COLLECTED</div><div style="font-weight:600">${fmt.currency(c.total_paid_inr)}</div></div>
        <div><div style="font-size:11px;color:var(--text-muted)">ORDERS</div><div style="font-weight:600">${c.total_orders}</div></div>
        <div><div style="font-size:11px;color:var(--text-muted)">AVG O2C</div><div style="font-weight:600">${fmt.days(c.avg_o2c_days)}</div></div>
      </div>
      <div style="margin-top:14px;display:flex;gap:6px;flex-wrap:wrap">
        ${c.cancelled_orders > 0 ? `<span class="badge badge-cancelled">${c.cancelled_orders} cancelled</span>` : ""}
        ${c.overdue_orders   > 0 ? `<span class="badge badge-warning">${c.overdue_orders} overdue</span>` : ""}
        ${c.unpaid_orders    > 0 ? `<span class="badge badge-info">${c.unpaid_orders} unpaid</span>` : ""}
      </div>
    `;
    grid.appendChild(card);
  });

  container.appendChild(grid);
}
