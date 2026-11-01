import type { Metadata } from "next";
import { Suspense } from "react";
import { LogoMark } from "@/components/Logo";
import { getDemoAccounts } from "@/lib/data";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = { title: "Log in" };

export default function LoginPage({ searchParams }: PageProps<"/login">) {
  return (
    <main className="relative min-h-[calc(100vh-1.5rem)] overflow-hidden bg-brand-50 px-4 pt-12 pb-16">
      {/* Soft arches echo the logo mark. */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 -left-32 size-[28rem] rounded-full border-[56px] border-brand-100" />
        <div className="absolute -right-24 -bottom-48 size-[32rem] rounded-full border-[64px] border-marigold-100/70" />
      </div>

      <div className="relative mx-auto flex max-w-md flex-col items-center">
        <div className="flex items-center gap-3">
          <LogoMark className="size-14" />
          <div className="leading-none">
            <p className="text-3xl font-bold tracking-tight text-brand-800">Univra</p>
            <p className="mt-1 text-[11px] font-medium tracking-[0.22em] text-stone-500 uppercase">
              University Management System
            </p>
          </div>
        </div>

        <Suspense fallback={<div className="mt-8 h-96 w-full rounded-2xl bg-white shadow-sm" />}>
          <LoginArea searchParams={searchParams} />
        </Suspense>
      </div>
    </main>
  );
}

async function LoginArea({ searchParams }: Pick<PageProps<"/login">, "searchParams">) {
  const [params, demoAccounts] = await Promise.all([searchParams, getDemoAccounts()]);
  const next = typeof params.next === "string" ? params.next : undefined;
  return (
    <LoginForm next={next} expired={params.expired === "1"} demoAccounts={demoAccounts} />
  );
}
