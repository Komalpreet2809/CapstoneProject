import { expect, test, type Page } from "@playwright/test";
import { expectDashboard } from "./personas";

// One student's session, in order: each step builds on the data the previous one left.
test.describe.configure({ mode: "serial" });

const REQUEST_ID = /^[A-Z]{3}\/[A-Z][a-z]{2}-\d{2}\/\d{5}$/;

test("dashboard: drive pop-up, then every card", async ({ page }) => {
  await page.goto("/");
  const drives = page.getByRole("dialog", { name: "Campus Drive Notifications" });
  await expect(drives).toBeVisible();
  await expect(drives.getByText("You are eligible for below drives")).toBeVisible();
  await drives.getByRole("button", { name: "Remind me later" }).click();
  await expect(drives).toBeHidden();

  // Snoozed: it stays away on the next visit.
  await page.reload();
  await expectDashboard(page);
  await expect(page.getByRole("dialog", { name: "Campus Drive Notifications" })).toBeHidden();
  for (const card of [
    "Happening",
    "My Messages",
    "My Courses",
    "Fee",
    "Pending Assignments",
    "Events",
    "Placement Details",
  ]) {
    await expect(page.getByRole("heading", { name: card, exact: true })).toBeVisible();
  }
  await expect(page.getByText(/CGPA : \d/)).toBeVisible();
});

test("mega-menu: grouped panel, then the shared placeholder page", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Academics" }).click();
  const panel = page.locator("#mega-panel");
  await expect(panel.getByRole("heading", { name: "Examination System" })).toBeVisible();
  await panel.getByRole("link", { name: "Examination Date Sheet" }).click();
  await expect(page).toHaveURL(/\/m\/exam-date-sheet$/);
  await expect(page.getByRole("heading", { level: 1, name: "Examination Date Sheet" })).toBeVisible();
  await expect(page.getByText("This page isn’t part of the demo yet")).toBeVisible();
});

test("menu search: '/' focuses it, keywords match, and ☆ pins a Quick Link", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("combobox", { name: "Search the menu" });
  await expect(search).toBeVisible();
  await expect(async () => {
    await page.keyboard.press("/");
    await expect(search).toBeFocused({ timeout: 500 });
  }).toPass();

  await search.fill("hazri"); // Hindi keyword for attendance
  await expect(page.getByRole("option", { name: /View Attendance/ })).toBeVisible();
  await page.getByRole("button", { name: "Add to Quick Links" }).first().click();
  await search.press("Enter");
  await expect(page).toHaveURL(/\/attendance$/); // a real page since M3

  await page.getByRole("button", { name: "Quick Links" }).click();
  await expect(page.locator("#mega-panel").getByRole("link", { name: "View Attendance" })).toBeVisible();
});

async function logRequest(page: Page, sub: string, title: string, description: string) {
  await page.getByRole("button", { name: "Agree & Proceed" }).click();
  await page.getByRole("radio", { name: /^Library/ }).check({ force: true });
  await page.getByLabel("Sub-category").selectOption(sub);
  await page.getByLabel("Title", { exact: true }).fill(title);
  await page.getByLabel("Description", { exact: true }).fill(description);
  await page.getByRole("button", { name: "Submit request" }).click();
}

test("RMS: log a request; a similar one offers a note on it instead", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Student Services" }).click();
  await page.locator("#mega-panel").getByRole("link", { name: "Log Request" }).click();
  await expect(page).toHaveURL(/\/rms$/);
  await expect(page.getByText("Relationship Management System")).toBeVisible();

  const details = [
    "Book Not Available",
    "Reference book missing",
    "The reference copy of the course book is not on the shelf.",
  ] as const;
  await logRequest(page, ...details);
  await expect(page.getByRole("heading", { name: "Request logged" })).toBeVisible();
  const requestId = (await page.getByText(REQUEST_ID).textContent())!;
  expect(requestId).toMatch(/^LIB\//);

  await page.getByRole("button", { name: "Log another request" }).click();
  await logRequest(page, ...details);
  await expect(page.getByText("You already have an open request like this one")).toBeVisible();
  await expect(page.getByText(requestId, { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Add a note to that request" }).click();
  await expect(page).toHaveURL(/tab=history/);
  await page.getByLabel("Add a note").fill("The second volume is missing too.");
  await page.getByRole("button", { name: "Add note" }).click();
  await expect(page.getByText("Note added.")).toBeVisible();
  const card = page.locator("article", { hasText: requestId });
  await expect(card.getByText("The second volume is missing too.")).toBeVisible();
});

test("RMS History: 'not resolved' feedback reopens a closed request", async ({ page }) => {
  await page.goto("/rms?tab=history&status=closed");
  const awaiting = page
    .locator("article")
    .filter({ has: page.getByRole("link", { name: "Feedback" }) })
    .first();
  const requestId = (await awaiting.getByText(REQUEST_ID).textContent())!;
  await awaiting.getByRole("link", { name: "Feedback" }).click();

  const card = page.locator("article", { hasText: requestId });
  await card.getByRole("radio", { name: "No, not resolved" }).check({ force: true });
  await card.getByRole("radio", { name: "2 of 5" }).check({ force: true });
  await card.getByPlaceholder("Comment (optional)").fill("The light flickers again at night.");
  await card.getByRole("button", { name: "Submit feedback" }).click();
  // Reopened, so it leaves the Closed list.
  await expect(card).toBeHidden();

  await page.goto("/rms?tab=history&status=open");
  const reopened = page.locator("article", { hasText: requestId });
  await expect(reopened.getByText("Reopened")).toBeVisible();
  await expect(reopened.getByText(/not resolved/)).toBeVisible();
});
