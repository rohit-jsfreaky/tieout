/**
 * The only place the desk talks to the API. No engine logic, no rules, no
 * thresholds — those live in `backend/src/tieout/engine/`.
 *
 * Ten routes and one stream. Every function here does exactly one HTTP call and
 * hands back the shape `lib/api-types.ts` describes; nothing is reshaped, merged
 * or derived on the way through, so a number on the screen is a number the engine
 * published.
 */

import type {
  AuthorityResponse,
  DecideRequest,
  DecideResponse,
  DoneEvent,
  EngineEvent,
  EventKind,
  ExceptionDetail,
  Metrics,
  PoliciesResponse,
  QueueResponse,
  ResetResponse,
  WorkAccepted,
} from "./api-types";
import { EVENT_KINDS } from "./api-types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8700";

/** What the API said went wrong, rather than "Failed to fetch". */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      `Tieout is not answering on ${API_BASE}. Start it with \`python -m tieout.api\`.`,
    );
  }
  if (!response.ok) {
    throw new ApiError(response.status, await detail(response));
  }
  return (await response.json()) as T;
}

/** FastAPI puts the readable half of a 4xx in `detail`. Use it, don't bury it. */
async function detail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      return String((body as { detail: unknown }).detail);
    }
  } catch {
    /* not JSON — fall through to the status line */
  }
  return `${response.status} ${response.statusText}`;
}

/** GET /queue — a fresh three-way match, then the exceptions that broke. */
export function getQueue(): Promise<QueueResponse> {
  return request<QueueResponse>("GET", "/queue");
}

/** GET /exceptions/{id} — the evidence pack, the decision, and the rule it cited. */
export function getException(id: string): Promise<ExceptionDetail> {
  return request<ExceptionDetail>("GET", `/exceptions/${id}`);
}

/** POST /exceptions/{id}/work — 202; the facts arrive on the stream. */
export function workException(id: string): Promise<WorkAccepted> {
  return request<WorkAccepted>("POST", `/exceptions/${id}/work`);
}

/** POST /exceptions/{id}/decide — the one human touch, and the rule it teaches. */
export function decideException(
  id: string,
  decision: DecideRequest,
): Promise<DecideResponse> {
  return request<DecideResponse>("POST", `/exceptions/${id}/decide`, decision);
}

/** GET /policies — every rule and version, with what has cited it. */
export function getPolicies(): Promise<PoliciesResponse> {
  return request<PoliciesResponse>("GET", "/policies");
}

/** GET /authority — the delegation-of-authority matrix, exactly as the engine holds it. */
export function getAuthority(): Promise<AuthorityResponse> {
  return request<AuthorityResponse>("GET", "/authority");
}

/** GET /metrics — counted from the store on every request, never typed in. */
export function getMetrics(): Promise<Metrics> {
  return request<Metrics>("GET", "/metrics");
}

/** POST /reset — the world, the memory, the session and the screenshots to zero. */
export function resetWorld(): Promise<ResetResponse> {
  return request<ResetResponse>("POST", "/reset");
}

/**
 * The URL for a `Fact.screenshot`.
 *
 * The engine stores an absolute path on its own machine (`~/.tieout/screenshots/
 * E1-PO-1042.png`, or the Windows spelling with backslashes). A browser cannot
 * open either, so the desk sends the file name to `GET /screenshots/{name}`.
 */
export function screenshotUrl(path: string): string {
  const name = path.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? "";
  return `${API_BASE}/screenshots/${encodeURIComponent(name)}`;
}

export interface StreamHandlers {
  onEvent: (event: EngineEvent) => void;
  onDone: (done: DoneEvent) => void;
  onError: (message: string) => void;
}

/**
 * GET /exceptions/{id}/events — the engine's own events, live.
 *
 * Each message is named by the event's own `kind`, so there is no `message`
 * listener to hang anything on: subscribe to the twelve kinds and to the stream's
 * own `done`. Returns the function that closes it.
 */
export function streamException(
  id: string,
  handlers: StreamHandlers,
): () => void {
  const source = new EventSource(`${API_BASE}/exceptions/${id}/events`);
  let closed = false;

  const close = () => {
    if (!closed) {
      closed = true;
      source.close();
    }
  };

  for (const kind of EVENT_KINDS) {
    source.addEventListener(kind, (message) => {
      handlers.onEvent(parse<EngineEvent>(message, kind));
    });
  }

  source.addEventListener("done", (message) => {
    handlers.onDone(parse<DoneEvent>(message, "done"));
    close();
  });

  source.onerror = () => {
    // EventSource reconnects by itself; on a run that is already over that is a
    // loop, so the desk closes the stream and says so once.
    if (!closed) {
      close();
      handlers.onError("the event stream dropped");
    }
  };

  return close;
}

function parse<T>(message: MessageEvent, kind: EventKind | "done"): T {
  try {
    return JSON.parse(message.data as string) as T;
  } catch {
    throw new ApiError(0, `unreadable ${kind} message on the stream`);
  }
}
