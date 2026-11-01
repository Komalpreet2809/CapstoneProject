import { NextResponse, type NextRequest } from "next/server";
import { isSameOrigin } from "@/lib/sameOrigin";
import { getToken } from "@/lib/session";
import { textTurn } from "@/lib/voice";

/** Typed questions from the widget (the text fallback). Streams the agent's NDJSON events. */
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = await getToken();
  if (!token) return NextResponse.json({ detail: "Not signed in" }, { status: 401 });

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const sessionId = typeof body?.session_id === "string" ? body.session_id : "";
  const text = typeof body?.text === "string" ? body.text.trim().slice(0, 500) : "";
  const pageId = typeof body?.page_id === "string" ? body.page_id.slice(0, 80) : null;
  if (!sessionId || !text) {
    return NextResponse.json({ detail: "session_id and text are required" }, { status: 422 });
  }

  let upstream: Response;
  try {
    upstream = await textTurn(sessionId, token, text, pageId);
  } catch {
    return NextResponse.json({ detail: "Assistant unavailable" }, { status: 503 });
  }
  if (!upstream.ok || !upstream.body) {
    const status = upstream.status === 404 ? 404 : 503;
    return NextResponse.json({ detail: "Assistant unavailable" }, { status });
  }
  return new Response(upstream.body, {
    headers: { "Content-Type": "application/x-ndjson", "Cache-Control": "no-store" },
  });
}
