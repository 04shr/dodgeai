// ── Sidebar — navigation shell ─────────────────────────
const ICONS = {
  "#/":          `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  "#/lifecycle": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><path d="M7 12h3m3 0h3"/></svg>`,
  "#/issues":    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>`,
  "#/customers": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
  "#/ai":        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 100 20A10 10 0 0012 2z"/><path d="M12 8v4l3 3"/></svg>`,
};

export function renderSidebar(container, routes) {
  const el = document.createElement("aside");
  el.className = "sidebar";
  el.innerHTML = `
    <div class="sidebar-logo">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
      O2C<span class="dot">.</span>Intel
    </div>
    <nav class="sidebar-nav">
      <span class="sidebar-section-label">Analytics</span>
      ${Object.entries(routes).map(([hash, r]) => `
        <div class="nav-item" data-route="${hash}" onclick="location.hash='${hash}'">
          ${ICONS[hash] ?? ""}
          <span>${r.label}</span>
        </div>
      `).join("")}
    </nav>
    <div style="padding:12px 16px;border-top:1px solid var(--border);margin-top:auto">
      <div style="font-size:11px;color:var(--text-muted)">SAP O2C · ABCD · INR</div>
    </div>
  `;
  container.appendChild(el);
}
