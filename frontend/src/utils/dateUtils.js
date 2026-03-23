// ── Date utilities ─────────────────────────────────────
export function daysBetween(a, b) {
  if (!a || !b) return null;
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}

export function isOverdue(billingDate, paymentTermDays = 30) {
  if (!billingDate) return false;
  const due = new Date(billingDate);
  due.setDate(due.getDate() + paymentTermDays);
  return new Date() > due;
}
