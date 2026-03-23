// ── AI Insights Page ───────────────────────────────────
import { setTopbarTitle } from "../components/shared/Topbar.js";
import { renderChatInterface } from "../components/ai/ChatInterface.js";
import { renderRecommendationPanel } from "../components/ai/RecommendationPanel.js";

export async function loadAI(container) {
  setTopbarTitle("AI Insights");
  container.innerHTML = "";

  const grid = document.createElement("div");
  grid.className = "grid-2";
  grid.style.height = "calc(100vh - 140px)";

  const leftCol = document.createElement("div");
  leftCol.style.cssText = "display:flex;flex-direction:column;gap:16px;";

  const h = document.createElement("div");
  h.innerHTML = `<div class="card-title">Natural language query</div>`;
  leftCol.appendChild(h);
  renderChatInterface(leftCol);

  const rightCol = document.createElement("div");
  rightCol.style.cssText = "display:flex;flex-direction:column;gap:16px;overflow-y:auto";
  const rh = document.createElement("div");
  rh.innerHTML = `<div class="card-title">AI-generated insights</div>`;
  rightCol.appendChild(rh);
  await renderRecommendationPanel(rightCol);

  grid.appendChild(leftCol);
  grid.appendChild(rightCol);
  container.appendChild(grid);
}
