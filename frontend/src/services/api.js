// ── API client — wraps all backend calls ───────────────
const BASE = import.meta?.env?.VITE_API_URL ?? "http://localhost:8000";

async function get(path, params = {}) {
  const qs  = new URLSearchParams(params).toString();
  const url = `${BASE}${path}${qs ? "?" + qs : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post(path, body = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  // KPIs
  getKpiSummary:   (filters) => get("/api/kpis/summary", filters),
  getCustomerKpis: ()        => get("/api/kpis/customers"),

  // Orders / Lifecycle
  getOrders:       (filters) => get("/api/orders", filters),
  getOrder:        (id)      => get(`/api/orders/${id}`),

  // Issues
  getIssues:       (filters) => get("/api/issues", filters),

  // Customers
  getCustomers:    ()        => get("/api/customers"),
  getCustomer:     (id)      => get(`/api/customers/${id}`),

  // AI
  queryAI:         (q)       => post("/api/ai/query", { question: q }),
  getRootCause:    (orderId) => post("/api/ai/root-cause", { order_id: orderId }),
  getInsights:     ()        => get("/api/ai/insights"),
};
