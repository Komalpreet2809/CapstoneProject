import { expect, test } from "@playwright/test";
import { closeDrivePopup } from "./personas";

test("assistant: a typed question gets an answer and an attendance card", async ({ page }) => {
  await page.goto("/");
  await closeDrivePopup(page);
  await page.getByRole("button", { name: "Open VoiceServe voice assistant" }).click();
  const panel = page.getByRole("dialog", { name: "VoiceServe assistant" });
  await expect(panel).toBeVisible();

  await panel.getByRole("textbox", { name: "Type a question" }).fill(
    "What's my attendance in Computer Networks?",
  );
  await panel.getByRole("button", { name: "Send" }).click();

  // The spoken-style answer arrives as a chat bubble; its first sentence also heads the card.
  await expect(panel.locator(".bubble.agent")).toContainText(
    /In CSE 326, Computer Networks, you've attended \d+ of \d+ classes/,
  );
  const card = panel.getByRole("region", { name: "Attendance" });
  await expect(card).toBeVisible();
  await expect(card.getByText("CSE326")).toBeVisible();

  await card.getByRole("link", { name: "Open attendance" }).click();
  await expect(page).toHaveURL(/\/attendance$/);
  await expect(page.getByRole("heading", { name: "View Attendance" })).toBeVisible();
  await expect(page.getByRole("row", { name: /CSE326/ })).toBeVisible();
});

test("assistant: out-of-scope questions get a polite refusal", async ({ page }) => {
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Open VoiceServe voice assistant" }).click();
  const panel = page.getByRole("dialog", { name: "VoiceServe assistant" });
  await panel.getByRole("textbox", { name: "Type a question" }).fill("Tell me a joke");
  await panel.getByRole("button", { name: "Send" }).click();
  await expect(panel.locator(".bubble.agent")).toContainText(
    "Sorry, I can only help with your student portal.",
  );
});
