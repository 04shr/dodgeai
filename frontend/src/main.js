// ── O2C Intelligence — Client Entry Point ──────────────
// Simple hash-based router; no framework required.

import { renderSidebar } from "./components/shared/Sidebar.js";
import { renderTopbar }  from "./components/shared/Topbar.js";
import { loadDashboard } from "./pages/Dashboard.js";
import { loadLifecycle } from "./pages/Lifecycle.js";
import { loadIssues }    from "./pages/Issues.js";
import { loadAI }        from "./pages/AIInsights.js";
import { loadCustomers } from "./pages/Customers.js";

const ROUTES = {
  "#/":          { label: "Dashboard",   loader: loadDashboard },
  "#/lifecycle": { label: "Lifecycle",   loader: loadLifecycle },
  "#/issues":    { label: "Issues",      loader: loadIssues },
  "#/ai":        { label: "AI Insights", loader: loadAI },
  "#/customers": { label: "Customers",   loader: loadCustomers },
};

async function mount() {
  const app = document.getElementById("app");
  app.innerHTML = "";

  renderSidebar(app, ROUTES);

  const main = document.createElement("div");
  main.className = "main-content";
  app.appendChild(main);

  renderTopbar(main);

  const pageBody = document.createElement("div");
  pageBody.id = "page-body";
  pageBody.className = "page-body";
  main.appendChild(pageBody);

  await navigate();
}

async function navigate() {
  const hash   = location.hash || "#/";
  const route  = ROUTES[hash] || ROUTES["#/"];
  const body   = document.getElementById("page-body");

  // Update active nav item
  document.querySelectorAll(".nav-item").forEach(el => {
    el.classList.toggle("active", el.dataset.route === hash);
  });

  body.innerHTML = `<div class="spinner" style="margin:60px auto"></div>`;
  await route.loader(body);
}

window.addEventListener("hashchange", navigate);
mount();
