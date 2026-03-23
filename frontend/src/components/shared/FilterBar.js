// ── Filter bar — customer / stage / date filters ───────
// TODO: Build in Dashboard.js and Issues.js pages
// Exports a factory so pages can instantiate with their own filter configs.
export function buildFilterBar(container, config, onChange) {
  const bar = document.createElement("div");
  bar.className = "filter-bar";

  config.forEach(({ key, label, type, options }) => {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-secondary)";
    wrapper.textContent = label + " ";

    let input;
    if (type === "select") {
      input = document.createElement("select");
      options.forEach(([val, text]) => {
        const opt = document.createElement("option");
        opt.value = val; opt.textContent = text;
        input.appendChild(opt);
      });
    } else {
      input = document.createElement("input");
      input.type = type ?? "text";
      input.placeholder = label;
    }
    input.addEventListener("change", () => onChange(key, input.value));
    wrapper.appendChild(input);
    bar.appendChild(wrapper);
  });

  container.appendChild(bar);
  return bar;
}
