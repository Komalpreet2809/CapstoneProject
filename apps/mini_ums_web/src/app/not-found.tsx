import Link from "next/link";
import { LogoMark } from "@/components/Logo";

export default function NotFound() {
  return (
    <main className="flex min-h-[calc(100vh-1.5rem)] flex-col items-center justify-center gap-4 px-4 text-center">
      <LogoMark className="size-12" />
      <h1 className="text-2xl font-semibold text-stone-900">Page not found</h1>
      <p className="max-w-sm text-stone-600">
        That page doesn’t exist in the portal. Use the menu or search to find what you need.
      </p>
      <Link
        href="/"
        className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
      >
        Go to dashboard
      </Link>
    </main>
  );
}
