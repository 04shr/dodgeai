// ── Topbar — page header + global actions ──────────────
export function renderTopbar(container) {
  const el = document.createElement("header");
  el.className = "topbar";
  el.id = "topbar";
  el.innerHTML = `
    <div class="topbar-title" id="topbar-title">Dashboard</div>
    <div class="topbar-actions">
      <button class="btn btn-ghost" onclick="location.reload()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
        Refresh
      </button>
      <button class="btn btn-primary" onclick="location.hash='#/ai'">
        Ask AI
      </button>
    </div>
  `;
  container.appendChild(el);
}

export function setTopbarTitle(title) {
  const el = document.getElementById("topbar-title");
  if (el) el.textContent = title;
}
