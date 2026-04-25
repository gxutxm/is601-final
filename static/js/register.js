// Registration form — client-side validation + POST /users/register.
(function () {
  const form = document.getElementById("register-form");
  const statusEl = document.getElementById("status");
  const submitBtn = form.querySelector('[data-testid="btn-submit"]');

  function validate() {
    api.clearAllErrors(form);
    let ok = true;

    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const confirm = form["confirm-password"].value;

    if (username.length < 3) {
      api.setFieldError(form, "username", "Username must be at least 3 characters.");
      ok = false;
    }
    if (!api.EMAIL_RE.test(email)) {
      api.setFieldError(form, "email", "Enter a valid email address.");
      ok = false;
    }
    if (password.length < 8) {
      api.setFieldError(form, "password", "Password must be at least 8 characters.");
      ok = false;
    }
    if (confirm !== password) {
      api.setFieldError(form, "confirm-password", "Passwords do not match.");
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
    submitBtn.textContent = "Registering…";

    try {
      const { ok, status, data } = await api.request("/users/register", {
        method: "POST",
        body: {
          username: form.username.value.trim(),
          email: form.email.value.trim(),
          password: form.password.value,
        },
      });

      if (ok) {
        api.showStatus(
          statusEl,
          "Registration successful! Redirecting to login…",
          "success"
        );
        setTimeout(() => {
          window.location.href = "/login";
        }, 1200);
      } else if (status === 409) {
        api.showStatus(
          statusEl,
          "That username or email is already registered.",
          "error"
        );
      } else if (status === 422 && Array.isArray(data?.detail)) {
        const msgs = data.detail.map((d) => d.msg).join("; ");
        api.showStatus(statusEl, `Validation error: ${msgs}`, "error");
      } else {
        api.showStatus(
          statusEl,
          data?.detail || "Registration failed. Please try again.",
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
      submitBtn.textContent = "Register";
    }
  });
})();
