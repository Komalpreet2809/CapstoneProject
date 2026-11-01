"use server";

import { refresh } from "next/cache";
import { ApiError } from "@/lib/api";
import { asStudent } from "@/lib/session";
import type { DuplicateTicket, Ticket, TicketDetail } from "@/lib/types";

export type CreateState =
  | { kind: "idle" }
  | { kind: "error"; message: string }
  | { kind: "duplicate"; message: string; similar: Ticket }
  | { kind: "created"; ticket: Ticket };

export type FormState = { ok?: boolean; error?: string };

const TICKET_NUMBER = /^[0-9]{5}$/;

function isDuplicate(body: unknown): body is DuplicateTicket {
  return typeof body === "object" && body !== null && "similar" in body;
}

function failure(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.status < 500) return err.detail;
  return fallback;
}

export async function createTicket(_prev: CreateState, formData: FormData): Promise<CreateState> {
  const text = (name: string) => String(formData.get(name) ?? "").trim();
  const body = {
    category: text("category"),
    sub_category: text("sub_category"),
    block: text("block") || null,
    room: text("room") || null,
    title: text("title"),
    description: text("description"),
    declaration_version: text("declaration_version"),
    allow_duplicate: formData.get("allow_duplicate") === "true",
  };
  try {
    const ticket = await asStudent<Ticket>("/me/tickets", {
      method: "POST",
      body,
      headers: { "Idempotency-Key": text("idempotency_key") },
    });
    return { kind: "created", ticket };
  } catch (err) {
    if (err instanceof ApiError && err.status === 409 && isDuplicate(err.body)) {
      return { kind: "duplicate", message: err.body.detail, similar: err.body.similar };
    }
    // Same idempotency key on retry, so submitting again can't create a second request.
    return {
      kind: "error",
      message: failure(err, "We couldn’t confirm your request. It’s safe to submit again."),
    };
  }
}

export async function addNote(_prev: FormState, formData: FormData): Promise<FormState> {
  const number = String(formData.get("number") ?? "");
  if (!TICKET_NUMBER.test(number)) return { error: "Unknown request" };
  try {
    await asStudent<TicketDetail>(`/me/tickets/${number}/notes`, {
      method: "POST",
      body: { note: String(formData.get("note") ?? "").trim() },
    });
  } catch (err) {
    return { error: failure(err, "Couldn’t add your note. Please try again.") };
  }
  refresh();
  return { ok: true };
}

export async function giveFeedback(_prev: FormState, formData: FormData): Promise<FormState> {
  const number = String(formData.get("number") ?? "");
  if (!TICKET_NUMBER.test(number)) return { error: "Unknown request" };
  const resolved = formData.get("resolved");
  const rating = Number(formData.get("rating"));
  if ((resolved !== "yes" && resolved !== "no") || !(rating >= 1 && rating <= 5)) {
    return { error: "Say whether it was resolved and give a rating from 1 to 5." };
  }
  const comment = String(formData.get("comment") ?? "").trim();
  try {
    await asStudent<TicketDetail>(`/me/tickets/${number}/feedback`, {
      method: "POST",
      body: { resolved: resolved === "yes", rating, comment: comment || null },
    });
  } catch (err) {
    return { error: failure(err, "Couldn’t save your feedback. Please try again.") };
  }
  refresh();
  return { ok: true };
}
