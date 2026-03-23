// ── Order Detail Drawer — right-side panel ─────────────
// Shows full lifecycle timeline + KPIs for selected order
import { renderLifecycleFlow } from "./LifecycleFlow.js";
import { stageBadge } from "../shared/Badge.js";
import { fmt } from "../../utils/formatters.js";

export function openOrderDrawer(order) {
  let overlay = document.getElementById("drawer-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "drawer-overlay";
    overlay.className = "drawer-overlay";
    overlay.onclick = closeOrderDrawer;
    document.body.appendChild(overlay);

    const drawer = document.createElement("div");
    drawer.id = "order-drawer";
    drawer.className = "drawer";
    document.body.appendChild(drawer);
  }

  const drawer = document.getElementById("order-drawer");
  drawer.innerHTML = `
    <div class="drawer-header">
      <div>
        <div style="font-weight:600;font-size:15px">Order ${order.sales_order_id}</div>
        <div style="font-size:12px;color:var(--text-muted)">${order.customer_name ?? order.customer_id}</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        ${stageBadge(order.lifecycle_stage)}
        <button class="btn btn-ghost" onclick="window.closeOrderDrawer()" style="padding:4px 8px">✕</button>
      </div>
    </div>
    <div class="drawer-body" id="drawer-content"></div>
  `;

  const body = drawer.querySelector("#drawer-content");

  // Lifecycle visual
  const lfSection = document.createElement("div");
  lfSection.style.marginBottom = "24px";
  renderLifecycleFlow(lfSection, order);
  body.appendChild(lfSection);

  // Key metrics grid
  body.innerHTML += `
    <div class="grid-2" style="margin-bottom:20px">
      <div class="kpi-card"><div class="kpi-label">Order Value</div><div class="kpi-value">${fmt.currency(order.order_total_net_amount)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Total O2C Days</div><div class="kpi-value">${fmt.days(order.total_o2c_days)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Order → Delivery</div><div class="kpi-value">${fmt.days(order.order_to_delivery_days)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Billing → Payment</div><div class="kpi-value">${fmt.days(order.billing_to_payment_days)}</div></div>
    </div>
    <div style="font-size:13px;color:var(--text-secondary);line-height:1.8">
      <div><b>Payment Terms:</b> ${order.payment_terms}</div>
      <div><b>Order Date:</b> ${fmt.date(order.order_created_date)}</div>
      <div><b>Requested Delivery:</b> ${fmt.date(order.requested_delivery_date)}</div>
    </div>
  `;

  overlay.classList.add("open");
  drawer.classList.add("open");
}

export function closeOrderDrawer() {
  document.getElementById("drawer-overlay")?.classList.remove("open");
  document.getElementById("order-drawer")?.classList.remove("open");
}

window.closeOrderDrawer = closeOrderDrawer;
