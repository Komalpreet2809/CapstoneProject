import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/cookie";

const PUBLIC_PATHS = new Set(["/login", "/session-expired"]);

/**
 * Coarse gate only: no cookie means sign in first. Whether the token is still valid is
 * checked by the API on every call (see lib/session.ts).
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const signedIn = request.cookies.has(SESSION_COOKIE);

  if (!signedIn && !PUBLIC_PATHS.has(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = pathname === "/" ? "" : `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }
  if (signedIn && pathname === "/login") {
    const url = request.nextUrl.clone();
    url.pathname = "/";
    url.search = "";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  // Skip the health check, Next's assets and files with an extension (icons, images).
  matcher: ["/((?!api/|_next/|.*\\..*).*)"],
};
