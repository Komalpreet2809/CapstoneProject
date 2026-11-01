import { clearSession } from "@/lib/session";

/** Pages land here when the API rejects the token: clear the cookie, then sign in again. */
export async function GET() {
  await clearSession();
  // A relative Location: in the standalone server, request.nextUrl carries the bind address
  // (0.0.0.0), not the host the browser used.
  return new Response(null, { status: 307, headers: { Location: "/login?expired=1" } });
}
