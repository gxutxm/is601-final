import { test, expect, Page } from "@playwright/test";

/**
 * Helper: fill the registration form with the given fields.
 * Any key can be omitted to leave that field blank.
 */
async function fillRegister(
  page: Page,
  {
    username,
    email,
    password,
    confirm,
  }: { username?: string; email?: string; password?: string; confirm?: string }
) {
  if (username !== undefined)
    await page.getByTestId("input-username").fill(username);
  if (email !== undefined) await page.getByTestId("input-email").fill(email);
  if (password !== undefined)
    await page.getByTestId("input-password").fill(password);
  if (confirm !== undefined)
    await page.getByTestId("input-confirm-password").fill(confirm);
}

// Each test gets a unique username/email so reruns don't collide with a
// user who registered in an earlier pass of this same suite.
function uniqueSuffix() {
  return `${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
}

test.describe("Registration page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /create an account/i })).toBeVisible();
  });

  test("registers a brand-new user and redirects to /login", async ({
    page,
  }) => {
    const suffix = uniqueSuffix();
    await fillRegister(page, {
      username: `user_${suffix}`,
      email: `user_${suffix}@example.com`,
      password: "StrongPass123",
      confirm: "StrongPass123",
    });
    await page.getByTestId("btn-submit").click();

    // Success banner appears before the redirect.
    await expect(page.getByTestId("status")).toHaveText(
      /registration successful/i
    );
    await expect(page.getByTestId("status")).toHaveClass(/success/);

    // Redirect lands on /login within ~2s.
    await page.waitForURL("**/login", { timeout: 3000 });
  });

  test("blocks submit with short password (client-side)", async ({ page }) => {
    await fillRegister(page, {
      username: "shortpw_user",
      email: "shortpw@example.com",
      password: "abc", // too short
      confirm: "abc",
    });
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("error-password")).toHaveText(
      /at least 8 characters/i
    );
    // No network hit — we should still be on /register.
    expect(page.url()).toContain("/register");
  });

  test("blocks submit with invalid email format (client-side)", async ({
    page,
  }) => {
    await fillRegister(page, {
      username: "bademail_user",
      email: "not-an-email",
      password: "StrongPass123",
      confirm: "StrongPass123",
    });
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("error-email")).toHaveText(/valid email/i);
    expect(page.url()).toContain("/register");
  });

  test("blocks submit when passwords don't match (client-side)", async ({
    page,
  }) => {
    await fillRegister(page, {
      username: "mismatch_user",
      email: "mismatch@example.com",
      password: "StrongPass123",
      confirm: "DifferentPass456",
    });
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("error-confirm-password")).toHaveText(
      /do not match/i
    );
    expect(page.url()).toContain("/register");
  });

  test("shows 409 error when email already registered (server-side)", async ({
    page,
  }) => {
    // First registration succeeds
    const suffix = uniqueSuffix();
    const username = `dup_${suffix}`;
    const email = `dup_${suffix}@example.com`;
    await fillRegister(page, {
      username,
      email,
      password: "StrongPass123",
      confirm: "StrongPass123",
    });
    await page.getByTestId("btn-submit").click();
    await page.waitForURL("**/login", { timeout: 3000 });

    // Second attempt with SAME email should trigger the server's 409.
    await page.goto("/register");
    await fillRegister(page, {
      username: `${username}_b`, // different username, same email
      email,
      password: "StrongPass123",
      confirm: "StrongPass123",
    });
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("status")).toHaveText(/already registered/i);
    await expect(page.getByTestId("status")).toHaveClass(/error/);
  });
});
