// ── Stage Stepper — compact inline stage indicator ─────
// Usage: el.innerHTML = stageStepper(order.lifecycle_stage)
export function stageStepper(currentStage) {
  const stages = ["ordered", "delivered", "billed", "paid"];
  const ci = stages.indexOf(currentStage);
  return stages.map((s, i) =>
    `<span style="color:${i <= ci ? "var(--accent)" : "var(--text-muted)"}">
      ${i === 0 ? "" : " → "}${s}
    </span>`
  ).join("");
}
