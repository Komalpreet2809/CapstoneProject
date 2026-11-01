import { NextResponse, type NextRequest } from "next/server";
import { isSameOrigin } from "@/lib/sameOrigin";
import { getToken } from "@/lib/session";
import { VoiceError, createVoiceSession } from "@/lib/voice";

/** The widget starts a voice session here; the portal token stays on the server (D-025). */
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = await getToken();
  if (!token) return NextResponse.json({ detail: "Not signed in" }, { status: 401 });

  const body: unknown = await request.json().catch(() => ({}));
  const pageId =
    typeof body === "object" && body !== null && "page_id" in body && typeof body.page_id === "string"
      ? body.page_id.slice(0, 80)
      : null;
  try {
    return NextResponse.json(await createVoiceSession(token, pageId));
  } catch (err) {
    if (err instanceof VoiceError && err.status === 401) {
      return NextResponse.json({ detail: "Session expired" }, { status: 401 });
    }
    return NextResponse.json({ detail: "Assistant unavailable" }, { status: 503 });
  }
}
