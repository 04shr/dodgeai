// ── Root Cause Panel — LLM analysis for a specific order
// Called from OrderDetailDrawer when user clicks "Analyse"
import { api } from "../../services/api.js";

export async function renderRootCausePanel(container, orderId) {
  container.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;color:var(--text-muted);padding:12px 0">
      <div class="spinner"></div> Analysing order ${orderId}…
    </div>`;

  try {
    const res = await api.getRootCause(orderId);
    container.innerHTML = `
      <div style="font-size:13px;line-height:1.7;color:var(--text-secondary)">${res.analysis}</div>
      ${res.recommendations?.length ? `
        <div style="margin-top:14px">
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:8px">RECOMMENDATIONS</div>
          <ul style="padding-left:18px;font-size:13px;display:flex;flex-direction:column;gap:6px">
            ${res.recommendations.map(r => `<li>${r}</li>`).join("")}
          </ul>
        </div>` : ""}
    `;
  } catch (e) {
    container.innerHTML = `<span style="color:var(--danger);font-size:13px">Analysis failed: ${e.message}</span>`;
  }
}