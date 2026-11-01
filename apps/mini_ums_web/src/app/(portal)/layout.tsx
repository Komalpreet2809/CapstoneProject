import Link from "next/link";
import { Suspense, type ReactNode } from "react";
import { Logo } from "@/components/Logo";
import { Identity } from "@/components/shell/Identity";
import { Ribbon } from "@/components/shell/Ribbon";
import { Sidebar } from "@/components/shell/Sidebar";
import { TopNav } from "@/components/shell/TopNav";

/**
 * The signed-in frame. Static parts (logo, layout) prerender; everything that needs the
 * session or API data streams in behind its own boundary, so no part waits on another.
 */
export default function PortalLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[calc(100vh-1.5rem)] flex-col">
      <Suspense fallback={<div className="h-8 bg-brand-900" />}>
        <Ribbon />
      </Suspense>
      <header className="sticky top-0 z-40 border-b border-stone-200 bg-white shadow-sm">
        <div className="flex h-16 items-center gap-3 px-4 lg:gap-5 lg:px-6">
          <Link href="/" aria-label="Univra dashboard" className="shrink-0">
            <Logo />
          </Link>
          <Suspense fallback={<div className="flex-1" />}>
            <TopNav />
          </Suspense>
          {/* Same footprint as the loaded block, so the menus don't shift when it arrives. */}
          <Suspense
            fallback={
              <div className="flex shrink-0 items-center gap-2.5 py-1 pr-1 pl-2">
                <div className="hidden h-9 w-56 rounded-md bg-stone-100 xl:block" />
                <div className="size-10 rounded-full bg-stone-100" />
                <div className="size-4" />
              </div>
            }
          >
            <Identity />
          </Suspense>
        </div>
      </header>
      <div className="flex flex-1">
        <Suspense fallback={<div className="hidden w-24 bg-brand-800 md:block" />}>
          <Sidebar />
        </Suspense>
        <main className="min-w-0 flex-1 px-4 py-6 lg:px-8">
          <Suspense fallback={<PageSkeleton />}>{children}</Suspense>
        </main>
      </div>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="animate-pulse space-y-4" aria-busy="true" aria-label="Loading">
      <div className="h-8 w-64 rounded-lg bg-stone-200" />
      <div className="h-40 rounded-2xl bg-stone-200" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="h-48 rounded-2xl bg-stone-200" />
        <div className="h-48 rounded-2xl bg-stone-200" />
        <div className="h-48 rounded-2xl bg-stone-200" />
      </div>
    </div>
  );
}
