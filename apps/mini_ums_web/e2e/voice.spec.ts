import { expect, test } from "@playwright/test";
import { closeDrivePopup } from "./personas";

// Chrome's fake microphone plays e2e/fixtures/attendance-question.wav on a loop. In replay
// mode the worker's speech-to-text returns recorded transcripts and its text-to-speech is a
// tone, so this exercises the real LiveKit path without paid providers.

test("voice: a spoken question gets a spoken answer and a card; tapping the mic interrupts", async ({
  page,
}) => {
  await page.goto("/");
  await closeDrivePopup(page);
  const session = page.waitForResponse((r) => r.url().endsWith("/api/voice/session"));
  await page.getByRole("button", { name: "Open VoiceServe voice assistant" }).click();
  const body = (await (await session).json()) as { voice: { mode: string } | null };
  test.skip(body.voice?.mode !== "replay", "needs the stack in REPLAY_MODE (CI runs it so)");

  const panel = page.getByRole("dialog", { name: "VoiceServe assistant" });
  await expect(panel.getByRole("status")).toHaveText(/Listening/, { timeout: 15_000 });

  // The student stops talking -> end of turn -> reply sentences (spoken) and the card.
  await expect(panel.locator(".bubble.user").first()).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByRole("region", { name: "Attendance" }).first()).toBeVisible({
    timeout: 20_000,
  });
  await expect(panel.locator(".bubble.agent").first()).toContainText(/percent|classes/);

  // Barge-in: tapping the mic while the agent speaks stops it and listens again.
  await expect(panel.getByRole("status")).toHaveText(/Speaking/, { timeout: 15_000 });
  await panel.getByRole("button", { name: "Interrupt and speak" }).click();
  await expect(panel.getByRole("status")).toHaveText(/Listening/, { timeout: 2_000 });
});
