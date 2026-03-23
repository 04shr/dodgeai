// ── Lifecycle Flow — visual stage tracker for one order ─
// Shows: Ordered → Delivered → Billed → Paid (or Cancelled)
// Props: order object from unified_o2c_orders.csv

import { fmt } from "../../utils/formatters.js";

const STAGES = ["ordered", "delivered", "billed", "paid"];

export function renderLifecycleFlow(container, order) {
  const currentIdx = STAGES.indexOf(order.lifecycle_stage);

  const el = document.createElement("div");
  el.style.cssText = "display:flex;flex-direction:column;gap:16px;";

  const track = document.createElement("div");
  track.className = "lifecycle-track";

  STAGES.forEach((stage, i) => {
    const isDone    = i < currentIdx;
    const isActive  = i === currentIdx;
    const isCancelled = order.lifecycle_stage === "cancelled";

    const stageEl = document.createElement("div");
    stageEl.className = "lifecycle-stage";
    stageEl.innerHTML = `
      <div class="stage-node ${isDone ? "done" : isActive ? "active" : ""} ${isCancelled && i <= currentIdx ? "error" : ""}">
        ${isDone ? "✓" : STAGE_ICONS[stage]}
      </div>
    `;
    track.appendChild(stageEl);

    if (i < STAGES.length - 1) {
      const conn = document.createElement("div");
      conn.className = `stage-connector ${isDone ? "done" : ""}`;
      track.appendChild(conn);
    }
  });

  el.appendChild(track);

  // Stage labels row
  const labels = document.createElement("div");
  labels.style.cssText = "display:flex;justify-content:space-between;font-size:11px;color:var(--text-secondary);margin-top:4px;";
  STAGES.forEach(s => {
    const d = document.createElement("div");
    d.style.flex = "1";
    d.style.textAlign = "center";
    d.textContent = s.charAt(0).toUpperCase() + s.slice(1);
    labels.appendChild(d);
  });
  el.appendChild(labels);

  container.appendChild(el);
}

const STAGE_ICONS = {
  ordered:   "📋",
  delivered: "🚚",
  billed:    "🧾",
  paid:      "✅",
};
