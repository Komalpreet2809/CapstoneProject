import "server-only";

// Service-to-service calls for the voice widget (D-025). The portal token never leaves the
// server: the widget gets an opaque voice session id and, for voice, a LiveKit room token.
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || "http://localhost:8002";
const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:8003";
const INTERNAL_KEY = process.env.INTERNAL_API_KEY || "dev-internal-key";

const internal = { "Content-Type": "application/json", "X-Internal-Key": INTERNAL_KEY };

export type VoiceAccess = { url: string; token: string; mode: "live" | "replay" };

export type VoiceSession = {
  session_id: string;
  first_name: string;
  voice: VoiceAccess | null;
  voice_unavailable_reason?: string;
};

export class VoiceError extends Error {
  constructor(readonly status: number) {
    super(`voice service answered ${status}`);
  }
}

export async function createVoiceSession(apiToken: string, pageId: string | null) {
  const res = await fetch(`${ORCHESTRATOR_URL}/sessions`, {
    method: "POST",
    headers: internal,
    body: JSON.stringify({ api_token: apiToken, page_id: pageId }),
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new VoiceError(res.status);
  const session = (await res.json()) as { session_id: string; first_name: string };
  return { ...session, ...(await voiceAccess(session.session_id)) } satisfies VoiceSession;
}

/** A LiveKit token for the session's room. Text still works when voice can't be offered. */
async function voiceAccess(
  sessionId: string,
): Promise<Pick<VoiceSession, "voice" | "voice_unavailable_reason">> {
  try {
    const res = await fetch(`${GATEWAY_URL}/voice-tokens`, {
      method: "POST",
      headers: internal,
      body: JSON.stringify({ session_id: sessionId }),
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return { voice: null, voice_unavailable_reason: "unavailable" };
    const body = (await res.json()) as { voice: VoiceAccess | null; reason?: string };
    return { voice: body.voice, voice_unavailable_reason: body.reason };
  } catch {
    return { voice: null, voice_unavailable_reason: "unavailable" };
  }
}

/** Streams the orchestrator's NDJSON turn events straight through to the widget. */
export async function textTurn(
  sessionId: string,
  apiToken: string,
  text: string,
  pageId: string | null,
): Promise<Response> {
  return fetch(`${ORCHESTRATOR_URL}/sessions/${encodeURIComponent(sessionId)}/turns`, {
    method: "POST",
    headers: internal,
    body: JSON.stringify({ text, page_id: pageId, channel: "text", owner_token: apiToken }),
    signal: AbortSignal.timeout(20000),
  });
}
