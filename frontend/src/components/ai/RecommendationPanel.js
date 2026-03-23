// ── Recommendation Panel — system-wide suggestions ─────
// TODO: fetch from /api/ai/insights and render insight cards
import { renderInsightCard } from "./InsightCard.js";
import { spinner } from "../shared/Spinner.js";

export async function renderRecommendationPanel(container) {
  container.innerHTML = spinner("Generating AI insights…");
  container.innerHTML = `
    <div style="color:var(--text-muted);font-size:13px;padding:24px;text-align:center">
      AI insights will appear here once the backend AI layer is connected.
    </div>`;
}
