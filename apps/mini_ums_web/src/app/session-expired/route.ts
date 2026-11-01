import { NextResponse, type NextRequest } from "next/server";
import { clearSession } from "@/lib/session";

/** Pages land here when the API rejects the token: clear the cookie, then sign in again. */
export async function GET(request: NextRequest) {
  await clearSession();
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "?expired=1";
  return NextResponse.redirect(url);
}
