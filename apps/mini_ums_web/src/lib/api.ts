import "server-only";

// Compose points this at the internal service; the default suits `next dev` against `make up`.
const API_URL = process.env.MINI_UMS_API_URL || "http://localhost:8001";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
    readonly body: unknown,
  ) {
    super(`${status}: ${detail}`);
  }
}

type Options = {
  method?: "GET" | "POST";
  token?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

/** Calls the Mini UMS API from server code. The browser never talks to it directly. */
export async function api<T>(path: string, { method = "GET", token, body, headers }: Options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
    headers: {
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return undefined as T;
  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, detailOf(data) ?? res.statusText, data);
  return data as T;
}

/** FastAPI errors carry `detail` as a string, or as a list of validation errors. */
function detailOf(data: unknown): string | undefined {
  if (!data || typeof data !== "object" || !("detail" in data)) return undefined;
  const { detail } = data as { detail: unknown };
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
    return detail[0].msg.replace(/^Value error, /, "");
  }
  return undefined;
}
