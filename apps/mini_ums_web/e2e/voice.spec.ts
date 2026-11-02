import { expect, test } from "@playwright/test";
import { closeDrivePopup } from "./personas";

// Chrome's fake microphone plays e2e/fixtures/attendance-question.wav on a loop. In replay
// mode (CI) the worker's speech-to-text returns recorded transcripts and its text-to-speech is
// a tone, so the real LiveKit path runs without paid providers. With provider keys it runs
// against real speech services (a few cents per run). The question is followed by silence up
// to 30 seconds, so the loop never talks over the reply and only the tap below interrupts.

test("voice: a spoken question gets a spoken answer and a card; tapping the mic interrupts", async ({
  page,
}) => {
  await page.goto("/");
  await closeDrivePopup(page);
  const session = page.waitForResponse((r) => r.url().endsWith("/api/voice/session"));
  await page.getByRole("button", { name: "Open VoiceServe voice assistant" }).click();
  const body = (await (await session).json()) as { voice: { mode: string } | null };
  test.skip(!body.voice, "needs voice: REPLAY_MODE or provider keys in .env");

  const panel = page.getByRole("dialog", { name: "VoiceServe assistant" });
  await expect(panel.getByRole("status")).toHaveText(/Listening/, { timeout: 15_000 });

  // The student stops talking -> end of turn -> reply sentences (spoken) and the card.
  await expect(panel.locator(".bubble.user").first()).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByRole("region", { name: "Attendance" }).first()).toBeVisible({
    timeout: 20_000,
  });
  // With real text-to-speech the transcript appears word by word, in step with the audio.
  await expect(panel.locator(".bubble.agent").first()).toContainText(/percent|classes/, {
    timeout: 15_000,
  });

  // Barge-in: tapping the mic while the agent speaks stops it and listens again.
  await expect(panel.getByRole("status")).toHaveText(/Speaking/, { timeout: 15_000 });
  await panel.getByRole("button", { name: "Interrupt and speak" }).click();
  await expect(panel.getByRole("status")).toHaveText(/Listening/, { timeout: 2_000 });
});

test("voice: tapping again ends the turn, and it is answered", async ({ page }) => {
  await page.goto("/");
  await closeDrivePopup(page);
  const session = page.waitForResponse((r) => r.url().endsWith("/api/voice/session"));
  await page.getByRole("button", { name: "Open VoiceServe voice assistant" }).click();
  const body = (await (await session).json()) as { voice: { mode: string } | null };
  // Replay speech-to-text has no live captions to wait on: it transcribes after the pause.
  test.skip(body.voice?.mode !== "live", "needs live voice: provider keys in .env");

  const panel = page.getByRole("dialog", { name: "VoiceServe assistant" });
  await expect(panel.getByRole("status")).toHaveText(/Listening/, { timeout: 15_000 });
  // Tap "done" while the question is still playing, before the agent could hear a pause.
  await expect(panel.locator(".bubble.user").first()).toContainText(/attendance/i, {
    timeout: 20_000,
  });
  await panel.getByRole("button", { name: "Stop speaking" }).click();
  await expect(panel.getByRole("region", { name: "Attendance" }).first()).toBeVisible({
    timeout: 20_000,
  });
  await expect(panel.locator(".bubble.agent").first()).toContainText(/percent|classes/, {
    timeout: 15_000,
  });
});
