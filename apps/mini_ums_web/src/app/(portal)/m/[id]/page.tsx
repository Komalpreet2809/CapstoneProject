import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";
import { Icon } from "@/components/icons";
import { getMenu } from "@/lib/data";
import { entryHref, findEntry } from "@/lib/menu";

/** One shared page for every menu entry whose real page isn't part of the demo yet. */
export default function PlaceholderPage({ params }: PageProps<"/m/[id]">) {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-2xl bg-stone-200" />}>
      <Placeholder params={params} />
    </Suspense>
  );
}

async function Placeholder({ params }: Pick<PageProps<"/m/[id]">, "params">) {
  const { id } = await params;
  const located = findEntry(await getMenu(), id);
  if (!located) notFound();
  const { menu, group, entry } = located;
  if (entry.route) redirect(entry.route);
  const siblings = group.entries.filter((e) => e.id !== entry.id);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-sm text-stone-500">
        <Link href="/" className="hover:text-brand-700">
          Dashboard
        </Link>
        <Icon name="chevronRight" className="size-4" />
        <span>{menu.label}</span>
        <Icon name="chevronRight" className="size-4" />
        <span>{group.label}</span>
      </nav>

      <section className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-stone-200">
        <div className="border-b border-stone-100 bg-brand-50 px-8 py-6">
          <h1 className="text-2xl font-semibold text-brand-900">{entry.label}</h1>
        </div>
        <div className="flex flex-col items-center px-8 py-12 text-center">
          <span className="grid size-14 place-items-center rounded-2xl bg-marigold-100 text-brand-800">
            <Icon name="grid" className="size-7" />
          </span>
          <h2 className="mt-4 text-lg font-semibold text-stone-800">
            This page isn’t part of the demo yet
          </h2>
          <p className="mt-1 max-w-md text-sm text-stone-600">
            {entry.label} sits in the menu exactly where students expect it. Its full page
            arrives in a later milestone.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/"
              className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
            >
              Back to dashboard
            </Link>
            <Link
              href="/rms"
              className="rounded-lg px-4 py-2 text-sm font-medium text-stone-700 ring-1 ring-stone-300 hover:bg-stone-50"
            >
              Need help? Log an RMS request
            </Link>
          </div>
        </div>
      </section>

      {siblings.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold tracking-wider text-stone-500 uppercase">
            More in {group.label}
          </h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {siblings.map((s) => (
              <li key={s.id}>
                <Link
                  href={entryHref(s)}
                  className="flex items-center justify-between rounded-xl bg-white px-4 py-3 text-sm font-medium text-stone-700 shadow-sm ring-1 ring-stone-200 hover:text-brand-800 hover:ring-brand-300"
                >
                  {s.label}
                  <Icon name="chevronRight" className="size-4 text-stone-400" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
