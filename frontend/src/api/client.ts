/** Typed API access (Increment 1 design, Section 10). Types come from the backend's OpenAPI document:
 *  `npm run gen:api` after exporting `src/api/openapi.json`. */
import createClient, { type Middleware } from "openapi-fetch";
import type { components, paths } from "./schema";

export type S<K extends keyof components["schemas"]> = components["schemas"][K];

export interface FieldProblem {
  field: string;
  code: string;
  message?: string;
}

/** An error answer of the API (application/problem+json); `detail` is already in the user's language. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public detail: string,
    public errors: FieldProblem[] = [],
    public extra: Record<string, unknown> = {},
  ) {
    super(detail || code);
  }

  fieldMessage(field: string): string | undefined {
    const e = this.errors.find((x) => x.field === field || x.field.endsWith(`.${field}`));
    return e ? e.message || e.code : undefined;
  }
}

const TOKEN_KEY = "internsync.token";
let onUnauthorized: () => void = () => {};

export const session = {
  get token(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set token(value: string | null) {
    try {
      if (value) sessionStorage.setItem(TOKEN_KEY, value);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage unavailable: the session lasts for this page only */
    }
  },
  onUnauthorized(handler: () => void) {
    onUnauthorized = handler;
  },
};

export function currentLanguage(): string {
  return document.documentElement.lang === "en" ? "en" : "ar";
}

function headers(): Record<string, string> {
  const h: Record<string, string> = { "Accept-Language": currentLanguage() };
  if (session.token) h.Authorization = `Bearer ${session.token}`;
  return h;
}

async function toError(response: Response): Promise<ApiError> {
  let body: Record<string, unknown> = {};
  try {
    body = await response.clone().json();
  } catch {
    /* not JSON */
  }
  const { code, detail, errors, title, status, type, ...extra } = body as Record<string, never>;
  void title;
  void status;
  void type;
  return new ApiError(response.status, code ?? "ERROR", detail ?? response.statusText, errors ?? [], extra);
}

const auth: Middleware = {
  async onRequest({ request }) {
    for (const [k, v] of Object.entries(headers())) request.headers.set(k, v);
    return request;
  },
  async onResponse({ response, request }) {
    if (response.status === 401 && !request.url.includes("/auth/login")) onUnauthorized();
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: "" });
api.use(auth);

/** Await an openapi-fetch call and return its data, or throw ApiError. */
export async function unwrap<T>(call: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await call;
  if (error !== undefined || !response.ok) throw await toError(response);
  return data as T;
}

/** Multipart requests (registration, uploads), which the typed client does not build for us. */
export async function sendForm<T>(method: "POST" | "PUT", path: string, form: FormData): Promise<T> {
  const response = await fetch(path, { method, body: form, headers: headers() });
  if (response.status === 401) onUnauthorized();
  if (!response.ok) throw await toError(response);
  return (await response.json()) as T;
}

/** A file served by the API (permission-checked), opened in a new tab. */
export async function openFile(fileId: string): Promise<void> {
  const response = await fetch(`/api/v1/files/${fileId}`, { headers: headers() });
  if (!response.ok) throw await toError(response);
  const url = URL.createObjectURL(await response.blob());
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

/** Development-only demo clock (not part of the typed API; mounted only when ENV is development). */
export async function demoClock(hours?: number): Promise<{ now: string; offset_hours: number } | null> {
  const response = await fetch(hours ? "/api/v1/dev/clock/advance" : "/api/v1/dev/clock", {
    method: hours ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: hours ? JSON.stringify({ hours }) : undefined,
  });
  return response.ok ? response.json() : null;
}
