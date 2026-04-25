import { test, expect, Page } from "@playwright/test";

/** Register + log in a fresh user, leave the page on /dashboard. */
async function freshLoggedInUser(page: Page) {
  const suffix = `${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  const username = `stats_${suffix}`;
  const email = `stats_${suffix}@example.com`;
  const password = "StrongPass123";

  const reg = await page.request.post("/users/register", {
    data: { username, email, password },
  });
  expect([201, 409]).toContain(reg.status());

  await page.goto("/login");
  await page.getByTestId("input-email").fill(email);
  await page.getByTestId("input-password").fill(password);
  await page.getByTestId("btn-submit").click();
  await page.waitForURL("**/dashboard", { timeout: 5000 });

  return { username, email, password };
}

async function createCalc(
  page: Page,
  a: number,
  b: number,
  type: string
) {
  await page.getByTestId("input-a").fill(String(a));
  await page.getByTestId("input-b").fill(String(b));
  await page.getByTestId("select-type").selectOption(type);
  await page.getByTestId("btn-create").click();
  await expect(page.getByTestId("status-create")).toBeVisible();
}

test.describe("Stats page", () => {
  test("requires auth — redirects to /login when no token", async ({ page }) => {
    // Navigate to a same-origin page first so we have a real document context
    // (localStorage isn't accessible on about:blank).
    await page.goto("/login");
    await page.evaluate(() => localStorage.removeItem("auth_token"));
    await page.goto("/stats");
    await page.waitForURL("**/login", { timeout: 5000 });
  });

  test("shows empty state when there are no calculations", async ({ page }) => {
    await freshLoggedInUser(page);
    await page.goto("/stats");

    await expect(page.getByTestId("stats-empty")).toBeVisible();
    await expect(page.getByTestId("stats-empty")).toContainText(
      /no calculations yet/i
    );
    await expect(page.getByTestId("stats-content")).toBeHidden();
  });

  test("shows aggregated metrics after creating calculations", async ({ page }) => {
    await freshLoggedInUser(page);

    // Create three Adds, one Multiply, one Power
    await createCalc(page, 1, 2, "Add");
    await createCalc(page, 3, 4, "Add");
    await createCalc(page, 5, 6, "Add");
    await createCalc(page, 2, 3, "Multiply");
    await createCalc(page, 2, 8, "Power");

    await page.goto("/stats");

    await expect(page.getByTestId("stats-content")).toBeVisible();
    await expect(page.getByTestId("stats-empty")).toBeHidden();

    await expect(page.getByTestId("stat-total")).toHaveText("5");
    await expect(page.getByTestId("stat-most-used")).toHaveText("Add");

    // Per-type breakdown
    await expect(page.getByTestId("type-count-Add")).toHaveText("3");
    await expect(page.getByTestId("type-count-Multiply")).toHaveText("1");
    await expect(page.getByTestId("type-count-Power")).toHaveText("1");
  });

  test("isolates stats between users", async ({ page }) => {
    // User A creates 2 calcs
    await freshLoggedInUser(page);
    await createCalc(page, 5, 5, "Multiply");
    await createCalc(page, 1, 1, "Add");

    // User A sees their stats
    await page.goto("/stats");
    await expect(page.getByTestId("stat-total")).toHaveText("2");

    // Log out, register fresh User B
    await page.getByTestId("btn-logout").click();
    await page.waitForURL("**/login");
    await freshLoggedInUser(page);

    // User B's stats start empty even though A's calcs exist in the DB
    await page.goto("/stats");
    await expect(page.getByTestId("stats-empty")).toBeVisible();
    await expect(page.getByTestId("stats-content")).toBeHidden();
  });

  test("dashboard topbar links to stats and back", async ({ page }) => {
    await freshLoggedInUser(page);

    await page.getByTestId("link-stats").click();
    await page.waitForURL("**/stats", { timeout: 5000 });

    await page.getByTestId("link-dashboard").click();
    await page.waitForURL("**/dashboard", { timeout: 5000 });
  });
});

test.describe("New operation types in BREAD UI", () => {
  test.beforeEach(async ({ page }) => {
    await freshLoggedInUser(page);
  });

  test("creates a Power calculation (2^10 = 1024)", async ({ page }) => {
    await createCalc(page, 2, 10, "Power");
    await expect(page.getByTestId("status-create")).toHaveText(/= 1024/);
  });

  test("creates a Modulus calculation (17 mod 5 = 2)", async ({ page }) => {
    await createCalc(page, 17, 5, "Modulus");
    await expect(page.getByTestId("status-create")).toHaveText(/= 2\b/);
  });

  test("creates a Root calculation (cube root of 27 = 3)", async ({ page }) => {
    await createCalc(page, 27, 3, "Root");
    await expect(page.getByTestId("status-create")).toHaveText(/= 3\b/);
  });

  test("blocks modulus by zero client-side", async ({ page }) => {
    await page.getByTestId("input-a").fill("10");
    await page.getByTestId("input-b").fill("0");
    await page.getByTestId("select-type").selectOption("Modulus");
    await page.getByTestId("btn-create").click();

    await expect(page.getByTestId("error-create")).toHaveText(
      /modulus by zero/i
    );
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(0);
  });

  test("blocks even-root of negative client-side", async ({ page }) => {
    await page.getByTestId("input-a").fill("-4");
    await page.getByTestId("input-b").fill("2");
    await page.getByTestId("select-type").selectOption("Root");
    await page.getByTestId("btn-create").click();

    await expect(page.getByTestId("error-create")).toHaveText(
      /even root of a negative/i
    );
  });
});