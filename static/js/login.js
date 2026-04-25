// Login form — client-side validation + POST /users/login, stores JWT in localStorage.
(function () {
  const form = document.getElementById("login-form");
  const statusEl = document.getElementById("status");
  const submitBtn = form.querySelector('[data-testid="btn-submit"]');

  function validate() {
    api.clearAllErrors(form);
    let ok = true;

    const email = form.email.value.trim();
    const password = form.password.value;

    if (!api.EMAIL_RE.test(email)) {
      api.setFieldError(form, "email", "Enter a valid email address.");
      ok = false;
    }
    if (password.length < 1) {
      api.setFieldError(form, "password", "Password is required.");
      ok = false;
    }

    return ok;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    api.clearStatus(statusEl);

    if (!validate()) {
      api.showStatus(statusEl, "Please fix the errors above.", "error");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in…";

    try {
      const { ok, status, data } = await api.request("/users/login", {
        method: "POST",
        body: {
          email: form.email.value.trim(),
          password: form.password.value,
        },
      });

      if (ok && data?.access_token) {
        api.setToken(data.access_token);
        api.showStatus(
          statusEl,
          "Login successful! Redirecting…",
          "success"
        );
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 800);
      } else if (status === 401) {
        api.showStatus(
          statusEl,
          "Invalid email or password.",
          "error"
        );
      } else if (status === 422) {
        api.showStatus(
          statusEl,
          "Please check your credentials.",
          "error"
        );
      } else {
        api.showStatus(
          statusEl,
          data?.detail || "Login failed. Please try again.",
          "error"
        );
      }
    } catch (err) {
      api.showStatus(
        statusEl,
        "Network error — is the server reachable?",
        "error"
      );
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Log in";
    }
  });
})();
