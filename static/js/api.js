// Shared API helper used by register.js, login.js, and dashboard.js.
// Everything lives on `window.api` to keep these simple script tags working.
(function () {
  const TOKEN_KEY = "auth_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  async function request(path, { method = "GET", body, auth = false } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = getToken();
      if (!token) throw new Error("Not authenticated");
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    let payload = null;
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      payload = await res.json().catch(() => null);
    }

    return { ok: res.ok, status: res.status, data: payload };
  }

  function showStatus(el, message, kind /* "success" | "error" */) {
    if (!el) return;
    el.textContent = message;
    el.classList.remove("hidden", "success", "error");
    el.classList.add(kind);
  }

  function clearStatus(el) {
    if (!el) return;
    el.textContent = "";
    el.classList.add("hidden");
    el.classList.remove("success", "error");
  }

  function setFieldError(formEl, fieldName, message) {
    const err = formEl.querySelector(`[data-testid="error-${fieldName}"]`);
    const input = formEl.querySelector(`[data-testid="input-${fieldName}"]`);
    if (err) err.textContent = message || "";
    if (input) {
      if (message) input.classList.add("invalid");
      else input.classList.remove("invalid");
    }
  }

  function clearAllErrors(formEl) {
    formEl.querySelectorAll(".field-error").forEach((n) => (n.textContent = ""));
    formEl.querySelectorAll("input").forEach((n) => n.classList.remove("invalid"));
  }

  // A simple email regex — server-side validation is the source of truth,
  // this just gives instant UI feedback.
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  window.api = {
    request,
    getToken,
    setToken,
    clearToken,
    showStatus,
    clearStatus,
    setFieldError,
    clearAllErrors,
    EMAIL_RE,
  };
})();
