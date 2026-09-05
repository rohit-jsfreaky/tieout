/**
 * The only place the desk talks to the API. No engine logic, no rules, no
 * thresholds — those live in `backend/src/tieout/engine/`.
 *
 * Phase 4a ships the shape only: every call carries its final signature and
 * throws until 4b puts a fetch behind `request`. Nothing here runs yet.
 */

import type {
  DecideRequest,
  DecideResponse,
  EvidencePack,
  Metrics,
  Policy,
  QueueItem,
} from "./api-types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8700";

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  throw new Error(
    `Tieout API not wired yet: ${method} ${API_BASE}${path}` +
      (body === undefined ? "" : " (with a payload)"),
  );
}

/** GET /queue — the five exceptions, with class, status and confidence. */
export function getQueue(): Promise<QueueItem[]> {
  return request<QueueItem[]>("GET", "/queue");
}

/** GET /exceptions/{id} — the evidence pack and the proposed decision, or the refusal. */
export function getExceptionPack(id: string): Promise<EvidencePack> {
  return request<EvidencePack>("GET", `/exceptions/${id}`);
}

/** POST /exceptions/{id}/work — start the investigation; facts arrive on the stream. */
export function workException(id: string): Promise<void> {
  return request<void>("POST", `/exceptions/${id}/work`);
}

/** POST /exceptions/{id}/decide — the one human touch. Returns the rule it created. */
export function decideException(
  id: string,
  decision: DecideRequest,
): Promise<DecideResponse> {
  return request<DecideResponse>("POST", `/exceptions/${id}/decide`, decision);
}

/** GET /policies — the learned rules, each with its approver and version. */
export function getPolicies(): Promise<Policy[]> {
  return request<Policy[]>("GET", "/policies");
}

/** GET /metrics — human touches, auto-cleared, refused, evidence items. */
export function getMetrics(): Promise<Metrics> {
  return request<Metrics>("GET", "/metrics");
}

/** POST /reset — world and engine store back to the seed. */
export function resetWorld(): Promise<void> {
  return request<void>("POST", "/reset");
}

/** The SSE endpoint for one investigation. Subscribed in 4b. */
export function eventsUrl(id: string): string {
  return `${API_BASE}/exceptions/${id}/events`;
}
