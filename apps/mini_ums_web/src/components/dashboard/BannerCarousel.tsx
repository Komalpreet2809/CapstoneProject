"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/icons";

export type Slide = { id: number; title: string; body: string; href: string | null };

const BACKDROPS = [
  "from-brand-800 via-brand-700 to-brand-500",
  "from-brand-950 via-brand-800 to-marigold-500",
  "from-stone-800 via-brand-900 to-brand-600",
  "from-brand-700 via-brand-600 to-marigold-400",
];
const INTERVAL_MS = 6000;

/** Rotating notice banners. Auto-advance pauses on hover/focus and when motion is reduced. */
export function BannerCarousel({ slides }: { slides: Slide[] }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || slides.length < 2) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % slides.length), INTERVAL_MS);
    return () => clearInterval(timer);
  }, [paused, slides.length]);

  const step = (delta: number) => setIndex((i) => (i + delta + slides.length) % slides.length);

  return (
    <section
      aria-roledescription="carousel"
      aria-label="Notices"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      className="relative h-48 overflow-hidden rounded-2xl shadow-sm sm:h-52"
    >
      {slides.map((slide, i) => (
        <div
          key={slide.id}
          role="group"
          aria-roledescription="slide"
          aria-label={`${i + 1} of ${slides.length}`}
          aria-hidden={i !== index}
          className={`absolute inset-0 flex flex-col justify-center bg-gradient-to-br px-8 py-6 text-white transition-opacity duration-700 sm:px-12 ${
            BACKDROPS[i % BACKDROPS.length]
          } ${i === index ? "opacity-100" : "pointer-events-none opacity-0"}`}
        >
          <div
            aria-hidden="true"
            className="absolute -right-10 -bottom-24 size-72 rounded-full border-[40px] border-white/10"
          />
          <p className="text-xs font-semibold tracking-[0.2em] text-marigold-200 uppercase">
            Notice
          </p>
          <h2 className="mt-2 max-w-xl text-2xl font-bold sm:text-3xl">{slide.title}</h2>
          <p className="mt-2 max-w-xl text-sm text-white/85 sm:text-base">{slide.body}</p>
          {slide.href && (
            <Link
              href={slide.href}
              tabIndex={i === index ? undefined : -1}
              className="mt-4 inline-flex w-fit items-center gap-1 rounded-full bg-white/15 px-4 py-1.5 text-sm font-medium ring-1 ring-white/30 backdrop-blur hover:bg-white/25"
            >
              Learn more <Icon name="arrowRight" className="size-4" />
            </Link>
          )}
        </div>
      ))}

      {slides.length > 1 && (
        <>
          <div className="absolute right-4 bottom-4 flex items-center gap-1.5">
            {slides.map((slide, i) => (
              <button
                key={slide.id}
                type="button"
                onClick={() => setIndex(i)}
                aria-label={`Show notice ${i + 1}`}
                aria-current={i === index}
                className={`h-2 rounded-full transition-all ${i === index ? "w-6 bg-white" : "w-2 bg-white/50 hover:bg-white/80"}`}
              />
            ))}
          </div>
          <div className="absolute top-4 right-4 flex gap-1">
            <button
              type="button"
              onClick={() => step(-1)}
              aria-label="Previous notice"
              className="grid size-8 place-items-center rounded-full bg-black/20 text-white hover:bg-black/35"
            >
              <Icon name="chevronLeft" className="size-4" />
            </button>
            <button
              type="button"
              onClick={() => step(1)}
              aria-label="Next notice"
              className="grid size-8 place-items-center rounded-full bg-black/20 text-white hover:bg-black/35"
            >
              <Icon name="chevronRight" className="size-4" />
            </button>
          </div>
        </>
      )}
    </section>
  );
}
