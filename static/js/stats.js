// Stats page — fetches /calculations/stats and renders the dashboard.
(function () {
  const usernameLabel = document.querySelector('[data-testid="username"]');
  const logoutBtn = document.getElementById("logout-btn");
  const emptyEl = document.getElementById("stats-empty");
  const contentEl = document.getElementById("stats-content");
  const barsEl = document.getElementById("type-bars");

  if (!api.getToken()) {
    window.location.href = "/login";
    return;
  }

  function fmt(n, digits = 2) {
    if (n === null || n === undefined) return "—";
    return Number(n).toFixed(digits).replace(/\.?0+$/, "");
  }

  async function loadUser() {
    const { ok, status, data } = await api.request("/users/me", { auth: true });
    if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
      return;
    }
    if (ok && data) usernameLabel.textContent = data.username;
  }

  async function loadStats() {
    const { ok, status, data } = await api.request("/calculations/stats", {
      auth: true,
    });
    if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
      return;
    }
    if (!ok) {
      emptyEl.textContent = "Failed to load stats.";
      emptyEl.classList.remove("hidden");
      return;
    }

    if (!data || data.total === 0) {
      emptyEl.classList.remove("hidden");
      return;
    }

    contentEl.classList.remove("hidden");
    document.querySelector('[data-testid="stat-total"]').textContent = data.total;
    document.querySelector('[data-testid="stat-most-used"]').textContent =
      data.most_used_type ?? "—";
    document.querySelector('[data-testid="stat-avg-result"]').textContent = fmt(
      data.avg_result
    );
    document.querySelector('[data-testid="stat-avg-a"]').textContent = fmt(data.avg_a);
    document.querySelector('[data-testid="stat-avg-b"]').textContent = fmt(data.avg_b);

    renderBars(data.by_type, data.total);
  }

  function renderBars(byType, total) {
    barsEl.innerHTML = "";
    // Sort by count descending so the most-used appears at the top.
    const entries = Object.entries(byType).sort((a, b) => b[1] - a[1]);
    for (const [type, count] of entries) {
      const pct = (count / total) * 100;
      const row = document.createElement("div");
      row.className = "type-row";
      row.dataset.testid = `type-row-${type}`;
      row.innerHTML = `
        <div class="type-name">${type}</div>
        <div class="type-bar-track">
          <div class="type-bar-fill" style="width: ${pct.toFixed(1)}%"></div>
        </div>
        <div class="type-count" data-testid="type-count-${type}">${count}</div>
      `;
      barsEl.appendChild(row);
    }
  }

  logoutBtn.addEventListener("click", () => {
    api.clearToken();
    window.location.href = "/login";
  });

  (async function init() {
    await loadUser();
    await loadStats();
  })();
})();
