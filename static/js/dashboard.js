// Dashboard — full BREAD UI for calculations.
// Uses window.api helpers from api.js for fetch + JWT handling.
(function () {
  const createForm = document.getElementById("create-form");
  const createStatus = document.getElementById("create-status");
  const tableBody = document.querySelector('[data-testid="calc-tbody"]');
  const emptyState = document.getElementById("calc-list-empty");
  const tableEl = document.getElementById("calc-table");
  const refreshBtn = document.getElementById("refresh-btn");
  const logoutBtn = document.getElementById("logout-btn");
  const usernameLabel = document.querySelector('[data-testid="username"]');

  const editModal = document.getElementById("edit-modal");
  const editForm = document.getElementById("edit-form");
  const editIdInput = document.getElementById("edit-id");
  const editA = document.getElementById("edit-a");
  const editB = document.getElementById("edit-b");
  const editType = document.getElementById("edit-type");
  const editCancel = document.getElementById("edit-cancel");
  const editError = document.querySelector('[data-testid="error-edit"]');

  // ---------- guards ----------

  if (!api.getToken()) {
    window.location.href = "/login";
    return;
  }

  // ---------- bootstrap ----------

  async function loadUser() {
    const { ok, status, data } = await api.request("/users/me", { auth: true });
    if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
      return;
    }
    if (ok && data) {
      usernameLabel.textContent = data.username;
    }
  }

  // ---------- Browse ----------

  async function loadCalcs() {
    const { ok, status, data } = await api.request("/calculations", {
      auth: true,
    });
    if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
      return;
    }
    if (!ok) {
      showCreateStatus("Failed to load calculations.", "error");
      return;
    }
    renderCalcs(data || []);
  }

  function renderCalcs(calcs) {
    tableBody.innerHTML = "";
    if (!calcs.length) {
      tableEl.classList.add("hidden");
      emptyState.classList.remove("hidden");
      return;
    }
    tableEl.classList.remove("hidden");
    emptyState.classList.add("hidden");

    for (const c of calcs) {
      const tr = document.createElement("tr");
      tr.dataset.testid = `calc-row-${c.id}`;
      tr.dataset.calcId = c.id;
      tr.innerHTML = `
        <td data-testid="calc-id-${c.id}">${c.id}</td>
        <td>${formatNum(c.a)}</td>
        <td data-testid="calc-type-${c.id}">${escapeHtml(c.type)}</td>
        <td>${formatNum(c.b)}</td>
        <td class="result" data-testid="calc-result-${c.id}">${formatNum(
        c.result
      )}</td>
        <td>${new Date(c.created_at).toLocaleString()}</td>
        <td class="actions">
          <button
            class="btn btn-secondary btn-small"
            data-action="edit"
            data-testid="btn-edit-${c.id}"
          >Edit</button>
          <button
            class="btn btn-danger"
            data-action="delete"
            data-testid="btn-delete-${c.id}"
          >Delete</button>
        </td>
      `;
      tableBody.appendChild(tr);
    }
  }

  function formatNum(n) {
    if (n === null || n === undefined) return "—";
    return Number.isInteger(n) ? String(n) : Number(n).toFixed(4).replace(/\.?0+$/, "");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  // ---------- Add ----------

  function validateCreate() {
    const a = createForm.querySelector("#create-a").value;
    const b = createForm.querySelector("#create-b").value;
    const type = createForm.querySelector("#create-type").value;
    const errEl = createForm.querySelector('[data-testid="error-create"]');
    errEl.textContent = "";

    if (a === "" || Number.isNaN(Number(a))) {
      errEl.textContent = "First number must be a valid number.";
      return null;
    }
    if (b === "" || Number.isNaN(Number(b))) {
      errEl.textContent = "Second number must be a valid number.";
      return null;
    }
    const aNum = Number(a);
    const bNum = Number(b);
    if (type === "Divide" && bNum === 0) {
      errEl.textContent = "Cannot divide by zero.";
      return null;
    }
    if (type === "Modulus" && bNum === 0) {
      errEl.textContent = "Cannot take modulus by zero.";
      return null;
    }
    if (type === "Root") {
      if (bNum === 0) {
        errEl.textContent = "Root degree (second number) cannot be zero.";
        return null;
      }
      if (aNum < 0 && bNum % 2 === 0) {
        errEl.textContent =
          "Cannot take an even root of a negative number.";
        return null;
      }
    }
    return { a: aNum, b: bNum, type };
  }

  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    api.clearStatus(createStatus);
    const payload = validateCreate();
    if (!payload) return;

    const { ok, status, data } = await api.request("/calculations", {
      method: "POST",
      auth: true,
      body: payload,
    });

    if (ok && data) {
      showCreateStatus(
        `Calculation created: ${payload.a} ${payload.type} ${payload.b} = ${data.result}`,
        "success"
      );
      createForm.reset();
      await loadCalcs();
    } else if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
    } else if (status === 422) {
      showCreateStatus(
        detailMessage(data) || "Validation error.",
        "error"
      );
    } else {
      showCreateStatus(
        data?.detail || "Failed to create calculation.",
        "error"
      );
    }
  });

  // ---------- Edit ----------

  tableBody.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const row = btn.closest("tr");
    const id = row.dataset.calcId;

    if (btn.dataset.action === "edit") {
      openEditModal(id);
    } else if (btn.dataset.action === "delete") {
      await deleteCalc(id);
    }
  });

  async function openEditModal(id) {
    // Read current values from the Read endpoint so we're sure we're editing
    // the server's state, not a stale row render.
    const { ok, data } = await api.request(`/calculations/${id}`, {
      auth: true,
    });
    if (!ok) {
      showCreateStatus("Failed to load calculation for editing.", "error");
      return;
    }

    editIdInput.value = data.id;
    editA.value = data.a;
    editB.value = data.b;
    editType.value = data.type;
    editError.textContent = "";
    editModal.classList.remove("hidden");
    editA.focus();
  }

  function closeEditModal() {
    editModal.classList.add("hidden");
    editForm.reset();
  }

  editCancel.addEventListener("click", closeEditModal);

  editModal.addEventListener("click", (e) => {
    // click outside the card closes the modal
    if (e.target === editModal) closeEditModal();
  });

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    editError.textContent = "";

    const id = editIdInput.value;
    const a = Number(editA.value);
    const b = Number(editB.value);
    const type = editType.value;

    if (Number.isNaN(a) || Number.isNaN(b)) {
      editError.textContent = "Both operands must be numbers.";
      return;
    }
    if (type === "Divide" && b === 0) {
      editError.textContent = "Cannot divide by zero.";
      return;
    }
    if (type === "Modulus" && b === 0) {
      editError.textContent = "Cannot take modulus by zero.";
      return;
    }
    if (type === "Root") {
      if (b === 0) {
        editError.textContent = "Root degree cannot be zero.";
        return;
      }
      if (a < 0 && b % 2 === 0) {
        editError.textContent =
          "Cannot take an even root of a negative number.";
        return;
      }
    }

    const { ok, status, data } = await api.request(`/calculations/${id}`, {
      method: "PUT",
      auth: true,
      body: { a, b, type },
    });

    if (ok) {
      closeEditModal();
      showCreateStatus(
        `Calculation #${id} updated — new result: ${data.result}`,
        "success"
      );
      await loadCalcs();
    } else if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
    } else if (status === 404) {
      editError.textContent = "Calculation not found.";
    } else if (status === 422) {
      editError.textContent = detailMessage(data) || "Validation error.";
    } else {
      editError.textContent = data?.detail || "Update failed.";
    }
  });

  // ---------- Delete ----------

  async function deleteCalc(id) {
    if (!window.confirm(`Delete calculation #${id}? This cannot be undone.`)) {
      return;
    }
    const { ok, status, data } = await api.request(`/calculations/${id}`, {
      method: "DELETE",
      auth: true,
    });
    if (ok) {
      showCreateStatus(`Calculation #${id} deleted.`, "success");
      await loadCalcs();
    } else if (status === 401) {
      api.clearToken();
      window.location.href = "/login";
    } else if (status === 404) {
      showCreateStatus("Calculation not found.", "error");
    } else {
      showCreateStatus(data?.detail || "Delete failed.", "error");
    }
  }

  // ---------- Helpers ----------

  function showCreateStatus(msg, kind) {
    api.showStatus(createStatus, msg, kind);
  }

  function detailMessage(data) {
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d) => d.msg).join("; ");
    }
    return data?.detail || null;
  }

  // ---------- Wire up + initial load ----------

  refreshBtn.addEventListener("click", loadCalcs);
  logoutBtn.addEventListener("click", () => {
    api.clearToken();
    window.location.href = "/login";
  });

  (async function init() {
    await loadUser();
    await loadCalcs();
  })();
})();
