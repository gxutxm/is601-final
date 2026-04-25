import { test, expect, Page } from "@playwright/test";

/** Register + log in a fresh user and leave the page on /dashboard. */
async function freshLoggedInUser(page: Page): Promise<{
  username: string;
  email: string;
  password: string;
}> {
  const suffix = `${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  const username = `calc_${suffix}`;
  const email = `calc_${suffix}@example.com`;
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
  a: string | number,
  b: string | number,
  type: "Add" | "Sub" | "Multiply" | "Divide"
) {
  await page.getByTestId("input-a").fill(String(a));
  await page.getByTestId("input-b").fill(String(b));
  await page.getByTestId("select-type").selectOption(type);
  await page.getByTestId("btn-create").click();
  await expect(page.getByTestId("status-create")).toBeVisible();
}

test.describe("Calculation BREAD UI", () => {
  test.beforeEach(async ({ page }) => {
    await freshLoggedInUser(page);
  });

  // ---------- Add + Browse ----------

  test("empty state shows when there are no calculations", async ({ page }) => {
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByTestId("empty-state")).toHaveText(/no calculations yet/i);
  });

  test("creates a calculation and it appears in the list", async ({ page }) => {
    await createCalc(page, 6, 7, "Multiply");
    await expect(page.getByTestId("status-create")).toHaveClass(/success/);
    await expect(page.getByTestId("status-create")).toHaveText(/= 42/);
    await expect(page.getByTestId("empty-state")).toBeHidden();

    // A row with result 42 should now exist
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Multiply");
    await expect(rows.first()).toContainText("42");
  });

  test("creates multiple calculations and browse returns them all", async ({
    page,
  }) => {
    await createCalc(page, 1, 2, "Add");
    await createCalc(page, 10, 4, "Sub");
    await createCalc(page, 8, 2, "Divide");

    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(3);
  });

  test("blocks divide-by-zero client-side", async ({ page }) => {
    await page.getByTestId("input-a").fill("10");
    await page.getByTestId("input-b").fill("0");
    await page.getByTestId("select-type").selectOption("Divide");
    await page.getByTestId("btn-create").click();

    await expect(page.getByTestId("error-create")).toHaveText(/cannot divide by zero/i);
    // No row should have been added
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(0);
  });

  test("blocks submit when operand is empty", async ({ page }) => {
    await page.getByTestId("input-a").fill("5");
    // b intentionally left blank
    await page.getByTestId("btn-create").click();
    await expect(page.getByTestId("error-create")).toHaveText(/valid number/i);
  });

  // ---------- Edit ----------

  test("edits a calculation and the result recomputes", async ({ page }) => {
    await createCalc(page, 2, 3, "Add");
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("5"); // 2 + 3

    // Click Edit on the first row
    const editBtn = page.locator('[data-testid^="btn-edit-"]').first();
    await editBtn.click();
    await expect(page.getByTestId("edit-modal")).toBeVisible();

    // Change operands + op
    await page.getByTestId("edit-input-a").fill("10");
    await page.getByTestId("edit-input-b").fill("4");
    await page.getByTestId("edit-select-type").selectOption("Sub");
    await page.getByTestId("btn-edit-save").click();

    await expect(page.getByTestId("edit-modal")).toBeHidden();
    await expect(page.getByTestId("status-create")).toHaveText(/updated/i);

    const updated = rows.first();
    await expect(updated).toContainText("Sub");
    await expect(updated).toContainText("6"); // 10 - 4
  });

  test("edit modal blocks divide-by-zero", async ({ page }) => {
    await createCalc(page, 4, 2, "Divide");
    const editBtn = page.locator('[data-testid^="btn-edit-"]').first();
    await editBtn.click();

    await page.getByTestId("edit-input-b").fill("0");
    await page.getByTestId("btn-edit-save").click();

    await expect(page.getByTestId("error-edit")).toHaveText(/cannot divide by zero/i);
    await expect(page.getByTestId("edit-modal")).toBeVisible();
  });

  test("edit modal can be cancelled without changes", async ({ page }) => {
    await createCalc(page, 2, 3, "Add");
    const editBtn = page.locator('[data-testid^="btn-edit-"]').first();
    await editBtn.click();

    await page.getByTestId("edit-input-a").fill("999");
    await page.getByTestId("btn-edit-cancel").click();

    await expect(page.getByTestId("edit-modal")).toBeHidden();
    const row = page.locator('[data-testid^="calc-row-"]').first();
    await expect(row).toContainText("5"); // unchanged, still 2+3
  });

  // ---------- Delete ----------

  test("deletes a calculation", async ({ page, context }) => {
    await createCalc(page, 10, 5, "Add");
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(1);

    // Auto-accept the confirm() dialog the UI pops before deleting
    page.once("dialog", (d) => d.accept());

    await page.locator('[data-testid^="btn-delete-"]').first().click();

    await expect(rows).toHaveCount(0);
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByTestId("status-create")).toHaveText(/deleted/i);
  });

  test("delete cancellation keeps the row", async ({ page }) => {
    await createCalc(page, 1, 1, "Add");
    const rows = page.locator('[data-testid^="calc-row-"]');
    await expect(rows).toHaveCount(1);

    page.once("dialog", (d) => d.dismiss());
    await page.locator('[data-testid^="btn-delete-"]').first().click();

    // Still there
    await expect(rows).toHaveCount(1);
  });

  // ---------- Security (negative) ----------

  test("dashboard redirects to /login when token is removed mid-session", async ({
    page,
  }) => {
    await createCalc(page, 1, 2, "Add");

    // Wipe the token and reload — the dashboard's first action is to check
    // the token; without one, it redirects to /login immediately.
    await page.evaluate(() => localStorage.removeItem("auth_token"));
    await page.goto("/dashboard");

    await page.waitForURL("**/login", { timeout: 5000 });
  });

  test("user B cannot see user A's calculations", async ({ page, context }) => {
    // User A (the beforeEach user) creates one
    await createCalc(page, 5, 5, "Multiply");
    await expect(page.locator('[data-testid^="calc-row-"]')).toHaveCount(1);

    // Log out and register user B
    await page.getByTestId("btn-logout").click();
    await page.waitForURL("**/login");
    await freshLoggedInUser(page);

    // B's dashboard should be empty
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.locator('[data-testid^="calc-row-"]')).toHaveCount(0);
  });
});
