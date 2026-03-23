// ── Formatting helpers ─────────────────────────────────

export const fmt = {
  currency: (v) =>
    v == null ? "—"
    : "₹" + Number(v).toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 0 }),

  number: (v, dec = 0) =>
    v == null ? "—" : Number(v).toLocaleString("en-IN", { minimumFractionDigits: dec }),

  days: (v) =>
    v == null ? "—" : `${Math.round(v)}d`,

  date: (v) =>
    v ? new Date(v).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—",

  pct: (v) =>
    v == null ? "—" : `${Number(v).toFixed(1)}%`,

  stage: (s) => ({
    ordered:   "Ordered",
    delivered: "Delivered",
    billed:    "Billed",
    paid:      "Paid",
    cancelled: "Cancelled",
  }[s] ?? s),
};
