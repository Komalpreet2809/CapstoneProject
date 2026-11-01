"use server";

import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";
import { asStudent, clearSession, getToken, setSession } from "@/lib/session";
import type { LoginOut } from "@/lib/types";

export type LoginState = { error?: string; regNo?: string };

/** Only same-site paths, so `?next=` can't bounce a student to another site after login. */
function safeNext(value: FormDataEntryValue | null): string {
  return typeof value === "string" && /^\/(?![/\\])/.test(value) ? value : "/";
}

export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const regNo = String(formData.get("reg_no") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!regNo || !password) {
    return { error: "Enter your registration number and password.", regNo };
  }
  let out: LoginOut;
  try {
    out = await api<LoginOut>("/auth/login", {
      method: "POST",
      body: { reg_no: regNo, password },
    });
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 423)) {
      return { error: err.detail, regNo };
    }
    if (err instanceof ApiError && err.status === 422) {
      return { error: "Invalid registration number or password", regNo };
    }
    return { error: "The portal can't be reached right now. Please try again shortly.", regNo };
  }
  await setSession(out.token, out.expires_at);
  redirect(safeNext(formData.get("next")));
}

export async function logout() {
  const token = await getToken();
  if (token) await api("/auth/logout", { method: "POST", token }).catch(() => undefined);
  await clearSession();
  redirect("/login");
}

export async function acknowledgeDrives(driveIds: number[], action: "read" | "later") {
  await asStudent("/me/placement-drives/ack", {
    method: "POST",
    body: { drive_ids: driveIds, action },
  });
}
