import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/cookie";

const PUBLIC_PATHS = new Set(["/login", "/session-expired"]);

/**
 * Proxy redirects must be absolute. Build them from the Host the browser used: the standalone
 * server's own URL can carry its bind address (0.0.0.0) instead.
 */
function redirectTo(request: NextRequest, location: string) {
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  const proto = request.headers.get("x-forwarded-proto") ?? request.nextUrl.protocol.replace(":", "");
  return NextResponse.redirect(new URL(location, host ? `${proto}://${host}` : request.url));
}

/**
 * Coarse gate only: no cookie means sign in first. Whether the token is still valid is
 * checked by the API on every call (see lib/session.ts).
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const signedIn = request.cookies.has(SESSION_COOKIE);

  if (!signedIn && !PUBLIC_PATHS.has(pathname)) {
    const next = pathname === "/" ? "" : `?next=${encodeURIComponent(pathname + search)}`;
    return redirectTo(request, `/login${next}`);
  }
  if (signedIn && pathname === "/login") {
    return redirectTo(request, "/");
  }
  return NextResponse.next();
}

export const config = {
  // Skip the health check, Next's assets and files with an extension (icons, images).
  matcher: ["/((?!api/|_next/|.*\\..*).*)"],
};
