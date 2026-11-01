import type { NextRequest } from "next/server";

/**
 * Cookie-authenticated POST routes only accept same-origin requests. SameSite=Lax already keeps
 * the cookie off cross-site POSTs; this also refuses them outright.
 */
export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}
