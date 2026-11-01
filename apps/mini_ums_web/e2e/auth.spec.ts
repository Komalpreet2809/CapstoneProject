import { expect, test } from "@playwright/test";
import { LOCKED, NO_REQUESTS, PASSWORD, expectDashboard, logIn } from "./personas";

test("a wrong password is refused; the right one signs in, and log out ends the session", async ({
  page,
}) => {
  await page.goto("/login");
  await logIn(page, NO_REQUESTS, "not-the-password");
  await expect(page.locator("form").getByRole("alert")).toHaveText(/Invalid registration number or password/);
  await expect(page.getByLabel("Registration number")).toHaveValue(NO_REQUESTS);

  await logIn(page, NO_REQUESTS, PASSWORD);
  await expectDashboard(page);
  const drives = page.getByRole("dialog", { name: "Campus Drive Notifications" });
  await expect(drives).toBeVisible();
  await drives.getByRole("button", { name: "Close" }).click();

  await page.getByRole("button", { name: /VID:/ }).click();
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
});

test("a locked account is refused with the lockout message", async ({ page }) => {
  await page.goto("/login");
  await logIn(page, LOCKED, PASSWORD);
  await expect(page.locator("form").getByRole("alert")).toHaveText(/locked/i);
  await expect(page).toHaveURL(/\/login$/);
});

test("a protected page sends you to log in, then back to where you were going", async ({
  page,
}) => {
  await page.goto("/rms?tab=history");
  await expect(page).toHaveURL(/\/login\?next=/);
  await logIn(page, NO_REQUESTS, PASSWORD);
  await expect(page).toHaveURL(/\/rms\?tab=history$/);
  await expect(page.getByText("You haven’t logged any requests yet.")).toBeVisible();
});
