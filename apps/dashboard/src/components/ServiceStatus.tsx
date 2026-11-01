import { connection } from "next/server";
import { parseTargets, probe } from "@/lib/status";

export async function ServiceStatus() {
  await connection();
  const results = await Promise.all(parseTargets(process.env.STATUS_TARGETS).map((t) => probe(t)));
  const healthy = results.filter((r) => r.ok).length;

  return (
    <section>
      <p className="mb-3 text-sm text-slate-600">
        {healthy}/{results.length} services ready
      </p>
      <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
        {results.map((r) => (
          <li key={r.name} className="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3">
            <span
              className={`inline-block size-2.5 rounded-full ${r.ok ? "bg-emerald-500" : "bg-rose-500"}`}
              aria-hidden
            />
            <span className="w-36 font-medium">{r.name}</span>
            <span className={`text-sm ${r.ok ? "text-emerald-700" : "text-rose-700"}`}>
              {r.ok ? "ready" : (r.error ?? `HTTP ${r.httpStatus}`)}
            </span>
            <span className="text-xs text-slate-500">{r.ms} ms</span>
            {r.checks && (
              <span className="basis-full pl-6 text-xs text-slate-500 sm:basis-auto sm:pl-0">
                {Object.entries(r.checks)
                  .map(([name, c]) => `${name}: ${c.ok ? (c.detail ?? "ok") : c.error}`)
                  .join(" · ")}
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
