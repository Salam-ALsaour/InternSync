/** Screenshots of the user guide (Increment 5, RQ-5): `npx playwright test -c playwright.guide.config.ts`, against
 *  the Docker stack with fresh demo data. Not part of the test run. */
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: "guide.capture.ts",
  timeout: 300_000,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173", viewport: { width: 1366, height: 860 } },
});
