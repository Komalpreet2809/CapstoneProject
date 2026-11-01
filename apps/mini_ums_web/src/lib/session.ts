import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, api } from "./api";
import { SESSION_COOKIE } from "./cookie";

export async function getToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

export async function setSession(token: string, expiresAt: string) {
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    // Off for the local http stack; set SESSION_COOKIE_SECURE=true behind https.
    secure: process.env.SESSION_COOKIE_SECURE === "true",
    path: "/",
    expires: new Date(expiresAt),
  });
}

export async function clearSession() {
  (await cookies()).delete(SESSION_COOKIE);
}

type Call = { method?: "GET" | "POST"; body?: unknown; headers?: Record<string, string> };

/**
 * Calls the API as the signed-in student. No token sends the visitor to sign in; a token the
 * API no longer accepts clears the cookie first (a page can't delete cookies while rendering).
 */
export async function asStudent<T>(path: string, call: Call = {}): Promise<T> {
  const token = await getToken();
  if (!token) redirect("/login");
  try {
    return await api<T>(path, { ...call, token });
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) redirect("/session-expired");
    throw err;
  }
}
