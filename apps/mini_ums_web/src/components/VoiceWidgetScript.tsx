import Script from "next/script";
import { connection } from "next/server";

const DEFAULT_WIDGET_URL = "http://localhost:4100/widget.js";

/**
 * Loads the VoiceServe widget from its own origin, the way a real UMS would embed a
 * third-party script. The URL is read at request time so one image works in any environment.
 */
export async function VoiceWidgetScript() {
  await connection();
  const src = process.env.WIDGET_URL || DEFAULT_WIDGET_URL;
  return <Script src={src} strategy="afterInteractive" />;
}
