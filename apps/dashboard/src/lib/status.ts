export type Target = { name: string; url: string };

export type Probe = Target & {
  ok: boolean;
  httpStatus?: number;
  ms: number;
  checks?: Record<string, { ok: boolean; detail?: string; error?: string }>;
  error?: string;
};

// Used when running `next dev` on the host against `make up`; Compose sets STATUS_TARGETS.
const DEFAULT_TARGETS =
  "mini_ums_api=http://localhost:8001/ready," +
  "orchestrator=http://localhost:8002/ready," +
  "gateway=http://localhost:8003/ready," +
  "widget=http://localhost:4100/health," +
  "mini_ums_web=http://localhost:3000/api/health";

/** Parse `name=url,name=url` into targets, skipping malformed entries. */
export function parseTargets(raw: string | undefined): Target[] {
  return (raw || DEFAULT_TARGETS)
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean)
    .flatMap((entry) => {
      const eq = entry.indexOf("=");
      if (eq <= 0) return [];
      return [{ name: entry.slice(0, eq).trim(), url: entry.slice(eq + 1).trim() }];
    });
}

export async function probe(target: Target, timeoutMs = 2000): Promise<Probe> {
  const started = performance.now();
  try {
    const res = await fetch(target.url, {
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
    const body = await res.json().catch(() => null);
    return {
      ...target,
      ok: res.ok,
      httpStatus: res.status,
      ms: Math.round(performance.now() - started),
      checks: body?.checks,
    };
  } catch (err) {
    return {
      ...target,
      ok: false,
      ms: Math.round(performance.now() - started),
      error: err instanceof Error ? err.message : String(err),
    };
  }
}
