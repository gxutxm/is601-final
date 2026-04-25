import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright runs against a live FastAPI server.
 *
 * Locally: start `uvicorn app.main:app --reload` in one terminal, then run
 * `npm test` here. BASE_URL defaults to http://127.0.0.1:8000.
 *
 * In CI: the `webServer` block below auto-starts the FastAPI server using
 * a Postgres service container (see .github/workflows/ci.yml for env vars).
 */
const PORT = Number(process.env.PORT || 8000);
const BASE_URL = process.env.BASE_URL || `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // tests share a DB; run serially to avoid flakes
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // In CI we launch the API server ourselves; locally you run it yourself.
  webServer: process.env.CI
    ? {
        command:
          "cd .. && uvicorn app.main:app --host 127.0.0.1 --port 8000",
        url: BASE_URL,
        reuseExistingServer: false,
        timeout: 60_000,
        stdout: "pipe",
        stderr: "pipe",
      }
    : undefined,
});
