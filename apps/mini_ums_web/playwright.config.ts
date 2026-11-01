import { defineConfig, devices } from "@playwright/test";
import { HOSTELLER_STATE } from "./e2e/personas";

/**
 * End-to-end tests against the running stack (`make up`). They change data, so `make e2e`
 * re-seeds first and they run one at a time. Locally they drive the installed Chrome; CI
 * uses Playwright's own Chromium (`npx playwright install chromium`).
 */
const channel = process.env.E2E_CHANNEL ?? (process.env.CI ? undefined : "chrome");
const browser = {
  ...devices["Desktop Chrome"],
  channel,
  viewport: { width: 1440, height: 900 },
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "setup", testMatch: /\.setup\.ts$/, use: browser },
    {
      name: "signed-in",
      testMatch: /portal\.spec\.ts$/,
      dependencies: ["setup"],
      use: { ...browser, storageState: HOSTELLER_STATE },
    },
    { name: "signed-out", testMatch: /auth\.spec\.ts$/, use: browser },
  ],
});
