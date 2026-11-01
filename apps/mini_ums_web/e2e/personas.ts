import path from "node:path";
import { expect, type Page } from "@playwright/test";

// Seeded demo personas (apps/mini_ums_api/src/mini_ums_api/seed/personas.py). The password is
// the demo one the login page lists in development.
export const PASSWORD = process.env.E2E_PASSWORD ?? "Demo@1234";
export const HOSTELLER = "24100001"; // open Wi-Fi request, closed request awaiting feedback
export const NO_REQUESTS = "24100006"; // no requests yet; eligible placement drives
export const LOCKED = "24100005"; // every login refused

export const HOSTELLER_STATE = path.join(__dirname, ".auth", "hosteller.json");

export async function logIn(page: Page, regNo: string, password: string) {
  await page.getByLabel("Registration number").fill(regNo);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
}

/** The dashboard is up once its first section heading renders. */
export async function expectDashboard(page: Page) {
  await expect(page.getByRole("heading", { name: "Important Links" })).toBeVisible();
}
