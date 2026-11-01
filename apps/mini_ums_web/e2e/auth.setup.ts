import { expect, test as setup } from "@playwright/test";
import { HOSTELLER, HOSTELLER_STATE, PASSWORD, expectDashboard, logIn } from "./personas";

setup("sign in as the hosteller persona", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await logIn(page, HOSTELLER, PASSWORD);
  await expectDashboard(page);
  // The httpOnly session cookie is saved with the rest of the browser state.
  await page.context().storageState({ path: HOSTELLER_STATE });
});
