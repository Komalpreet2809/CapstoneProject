"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/icons";

type Item = { id: number; title: string; body: string; href: string | null };

const INTERVAL_MS = 7000;

/** Top strip: one announcement at a time, with « » to step through them. */
export function AnnouncementStrip({ items }: { items: Item[] }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || items.length < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % items.length), INTERVAL_MS);
    return () => clearInterval(timer);
  }, [paused, items.length]);

  const step = (delta: number) => setIndex((i) => (i + delta + items.length) % items.length);
  const item = items[index]!;
  const text = (
    <>
      <span className="font-semibold text-marigold-200">{item.title}</span>
      <span className="text-brand-50"> · {item.body}</span>
    </>
  );

  return (
    <div
      className="flex items-center bg-brand-900 text-sm"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <button
        type="button"
        onClick={() => step(-1)}
        aria-label="Previous announcement"
        className="px-3 py-1.5 text-brand-200 hover:text-white"
      >
        <Icon name="chevronsLeft" className="size-4" />
      </button>
      <p
        key={item.id}
        aria-live="polite"
        className="min-w-0 flex-1 animate-fade-in truncate text-center"
      >
        {item.href ? (
          <Link href={item.href} className="hover:underline">
            {text}
          </Link>
        ) : (
          text
        )}
      </p>
      <button
        type="button"
        onClick={() => step(1)}
        aria-label="Next announcement"
        className="px-3 py-1.5 text-brand-200 hover:text-white"
      >
        <Icon name="chevronsLeft" className="size-4 rotate-180" />
      </button>
    </div>
  );
}
