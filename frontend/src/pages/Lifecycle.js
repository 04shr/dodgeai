// ── Lifecycle Page ─────────────────────────────────────
import { setTopbarTitle } from "../components/shared/Topbar.js";
import { renderOrderTable } from "../components/lifecycle/OrderTable.js";
import { openOrderDrawer } from "../components/lifecycle/OrderDetailDrawer.js";
import { buildFilterBar } from "../components/shared/FilterBar.js";
import { spinner } from "../components/shared/Spinner.js";

export async function loadLifecycle(container) {
  setTopbarTitle("Lifecycle Tracker");
  container.innerHTML = spinner("Loading orders…");

  const orders = await fetch("../../data/processed/unified_o2c_orders.csv")
    .then(r => r.text())
    .then(csvToObjects);

  container.innerHTML = "";

  let filtered = [...orders];

  // Filter config
  const stages     = [...new Set(orders.map(o => o.lifecycle_stage))].sort();
  const customers  = [...new Set(orders.map(o => o.customer_id))];

  buildFilterBar(container, [
    { key: "stage",    label: "Stage",    type: "select",
      options: [["", "All stages"], ...stages.map(s => [s, s.charAt(0).toUpperCase()+s.slice(1)])] },
    { key: "customer", label: "Customer", type: "select",
      options: [["", "All customers"], ...customers.map(c => [c, c])] },
  ], (key, val) => {
    filtered = orders.filter(o => {
      if (key === "stage"    && val && o.lifecycle_stage !== val) return false;
      if (key === "customer" && val && o.customer_id     !== val) return false;
      return true;
    });
    tbody.innerHTML = "";
    renderOrderTable(container, filtered, openOrderDrawer);
  });

  const tbody = renderOrderTable(container, filtered, openOrderDrawer);
}

// ── CSV parser helper ───────────────────────────────────
function csvToObjects(csv) {
  const [headerLine, ...rows] = csv.trim().split("\n");
  const headers = headerLine.split(",");
  return rows.map(row => {
    const vals = row.split(",");
    return Object.fromEntries(headers.map((h, i) => [h, vals[i] ?? ""]));
  });
}
