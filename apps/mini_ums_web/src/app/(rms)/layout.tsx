import Link from "next/link";
import type { ReactNode } from "react";
import { Icon } from "@/components/icons";
import { Logo } from "@/components/Logo";

/** RMS is a module of its own: its own header and page, outside the portal shell. */
export default function RmsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[calc(100vh-1.5rem)] bg-gradient-to-b from-brand-600 to-brand-800">
      <header className="bg-white shadow-sm">
        <div className="mx-auto grid max-w-6xl grid-cols-[auto_1fr_auto] items-center gap-4 px-4 py-3 sm:grid-cols-[1fr_auto_1fr]">
          <Link href="/" aria-label="Univra dashboard" className="justify-self-start">
            <Logo />
          </Link>
          <p className="text-center text-base font-bold text-stone-900 sm:text-2xl">
            Relationship Management System <span className="text-marigold-500">(RMS)</span>
          </p>
          <Link
            href="/"
            className="flex items-center gap-1.5 justify-self-end text-sm font-medium text-stone-700 hover:text-brand-700"
          >
            <Icon name="home" className="size-4" />
            <span className="hidden sm:inline">Univra Home</span>
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
    </div>
  );
}
