// ── AI Chat Interface ──────────────────────────────────
// NL query panel — sends questions to /api/ai/query
import { api } from "../../services/api.js";

export function renderChatInterface(container) {
  const el = document.createElement("div");
  el.className = "chat-panel";
  el.style.cssText = "height:520px";
  el.innerHTML = `
    <div class="chat-messages" id="chat-messages">
      <div class="chat-bubble ai">
        👋 Ask me anything about your O2C data. Try:
        <ul style="margin:8px 0 0 16px;font-size:12px;opacity:.8">
          <li>Why are so many billing docs being cancelled?</li>
          <li>Which customers have the most payment delays?</li>
          <li>What orders are at risk right now?</li>
        </ul>
      </div>
    </div>
    <div class="chat-input-row">
      <input class="chat-input" id="chat-input" placeholder="Ask a question about your O2C data…" />
      <button class="btn btn-primary" id="chat-send">Send</button>
    </div>
  `;
  container.appendChild(el);

  const input   = el.querySelector("#chat-input");
  const send    = el.querySelector("#chat-send");
  const msgs    = el.querySelector("#chat-messages");

  async function sendMessage() {
    const q = input.value.trim();
    if (!q) return;
    input.value = "";

    // User bubble
    msgs.innerHTML += `<div class="chat-bubble user">${q}</div>`;

    // Typing indicator
    const typing = document.createElement("div");
    typing.className = "chat-bubble ai";
    typing.innerHTML = `<div class="spinner" style="width:14px;height:14px"></div>`;
    msgs.appendChild(typing);
    msgs.scrollTop = msgs.scrollHeight;

    try {
      const res = await api.queryAI(q);
      typing.innerHTML = res.answer ?? res.response ?? JSON.stringify(res);
    } catch (e) {
      typing.innerHTML = `<span style="color:var(--danger)">Error: ${e.message}</span>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
  }

  send.onclick = sendMessage;
  input.addEventListener("keydown", e => e.key === "Enter" && sendMessage());
}
