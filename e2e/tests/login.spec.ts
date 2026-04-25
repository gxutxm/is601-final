import { test, expect, Page } from "@playwright/test";

/** Register a user directly through the API so login tests don't depend on the register UI. */
async function registerViaApi(
  page: Page,
  username: string,
  email: string,
  password: string
) {
  const resp = await page.request.post("/users/register", {
    data: { username, email, password },
  });
  expect([201, 409]).toContain(resp.status());
}

function uniqueSuffix() {
  return `${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
}

test.describe("Login page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /log in/i })).toBeVisible();
  });

  test("logs in with valid credentials, stores JWT, redirects to dashboard", async ({
    page,
  }) => {
    const suffix = uniqueSuffix();
    const username = `login_${suffix}`;
    const email = `login_${suffix}@example.com`;
    const password = "StrongPass123";

    await registerViaApi(page, username, email, password);
    await page.goto("/login");

    await page.getByTestId("input-email").fill(email);
    await page.getByTestId("input-password").fill(password);
    await page.getByTestId("btn-submit").click();

    // Success banner
    await expect(page.getByTestId("status")).toHaveText(/login successful/i);
    await expect(page.getByTestId("status")).toHaveClass(/success/);

    // Redirect to dashboard
    await page.waitForURL("**/dashboard", { timeout: 3000 });

    // JWT should now be in localStorage
    const token = await page.evaluate(() => localStorage.getItem("auth_token"));
    expect(token).toBeTruthy();
    expect(token).toMatch(/^eyJ/); // JWT header always starts this way

    // Dashboard populates with the user's data
    await expect(page.getByTestId("username")).toHaveText(username);
  });

  test("shows 401 error for wrong password (server-side)", async ({ page }) => {
    const suffix = uniqueSuffix();
    const username = `wrongpw_${suffix}`;
    const email = `wrongpw_${suffix}@example.com`;

    await registerViaApi(page, username, email, "StrongPass123");
    await page.goto("/login");

    await page.getByTestId("input-email").fill(email);
    await page.getByTestId("input-password").fill("WrongPassword123");
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("status")).toHaveText(/invalid email or password/i);
    await expect(page.getByTestId("status")).toHaveClass(/error/);

    // Still on /login — no token stored
    expect(page.url()).toContain("/login");
    const token = await page.evaluate(() => localStorage.getItem("auth_token"));
    expect(token).toBeFalsy();
  });

  test("shows 401 for an unregistered email", async ({ page }) => {
    await page.getByTestId("input-email").fill("nobody@example.com");
    await page.getByTestId("input-password").fill("AnyPassword123");
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("status")).toHaveText(/invalid email or password/i);
    await expect(page.getByTestId("status")).toHaveClass(/error/);
    expect(page.url()).toContain("/login");
  });

  test("blocks submit when email is malformed (client-side)", async ({ page }) => {
    await page.getByTestId("input-email").fill("not-an-email");
    await page.getByTestId("input-password").fill("somepass");
    await page.getByTestId("btn-submit").click();

    await expect(page.getByTestId("error-email")).toHaveText(/valid email/i);
    expect(page.url()).toContain("/login");
  });

  test("dashboard redirects to /login when no token is stored", async ({ page }) => {
    await page.evaluate(() => localStorage.removeItem("auth_token"));
    await page.goto("/dashboard");
    await page.waitForURL("**/login", { timeout: 3000 });
  });

  test("logout clears the token and returns to /login", async ({ page }) => {
    const suffix = uniqueSuffix();
    const email = `logout_${suffix}@example.com`;
    const password = "StrongPass123";

    await registerViaApi(page, `logout_${suffix}`, email, password);
    await page.goto("/login");
    await page.getByTestId("input-email").fill(email);
    await page.getByTestId("input-password").fill(password);
    await page.getByTestId("btn-submit").click();
    await page.waitForURL("**/dashboard");

    await page.getByTestId("btn-logout").click();
    await page.waitForURL("**/login");

    const token = await page.evaluate(() => localStorage.getItem("auth_token"));
    expect(token).toBeFalsy();
  });
});
