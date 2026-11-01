import { useSyncExternalStore } from "react";

// Quick Links are personal pins, as in the real portal. They're a per-browser convenience,
// so they live in localStorage; every access is guarded (private mode, blocked storage).
const KEY = "univra:quick-links";
const CHANGED = "univra:quick-links-changed";
const NONE: string[] = [];

let lastRaw: string | null = null;
let lastValue: string[] = NONE;

function read(): string[] {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(KEY);
  } catch {
    return NONE;
  }
  if (raw !== lastRaw) {
    lastRaw = raw;
    try {
      const parsed: unknown = JSON.parse(raw ?? "[]");
      lastValue = Array.isArray(parsed) ? parsed.filter((v) => typeof v === "string") : NONE;
    } catch {
      lastValue = NONE;
    }
  }
  return lastValue;
}

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange);
  window.addEventListener(CHANGED, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGED, onChange);
  };
}

/** Pinned entry ids; empty during server rendering and hydration. */
export function useQuickLinks(): string[] {
  return useSyncExternalStore(subscribe, read, () => NONE);
}

export function toggleQuickLink(id: string) {
  const current = read();
  const next = current.includes(id) ? current.filter((v) => v !== id) : [...current, id];
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    return;
  }
  window.dispatchEvent(new Event(CHANGED));
}
