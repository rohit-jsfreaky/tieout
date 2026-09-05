/**
 * The shapes the API sends. Mirrored by hand from the routes in
 * `backend/PLAN.md` Phase 3; reconcile against `backend/src/tieout/api/schemas.py`
 * the moment 3a lands, and keep this the only file that describes them.
 *
 * `class` is a Python keyword, so the exception's class travels as
 * `exception_class`.
 */

export type ExceptionClass =
  | "short_ship"
  | "price_variance"
  | "missing_po"
  | "unknown";

export type ExceptionStatus =
  | "open"
  | "investigating"
  | "proposed"
  | "refused"
  | "decided"
  | "auto_cleared";

export type FactSource = "erp" | "inbox" | "portal";

export type DecisionAction = "approve" | "reject" | "edit";

/** GET /queue */
export interface QueueItem {
  id: string;
  vendor: string;
  invoice_id: string;
  amount: number;
  currency: string;
  exception_class: ExceptionClass;
  status: ExceptionStatus;
  confidence: number | null;
  /** Set when a learned rule cleared this one without a human. */
  cited_policy: string | null;
  approved_by: string | null;
}

/** One thing the agent saw, and where it saw it. Written only by evidence.py. */
export interface Fact {
  id: string;
  source: FactSource;
  locator: string;
  observed_at: string;
  summary: string;
  raw: string;
  /** Portal facts carry a screenshot; ERP and inbox facts do not. */
  screenshot: string | null;
}

export interface ProposedDecision {
  action: DecisionAction;
  summary: string;
  rationale: string;
  confidence: number;
  /** Set when the proposal came from a learned rule rather than a fresh look. */
  cited_policy: string | null;
  auto: boolean;
}

/** Refusing is an outcome, not an error: what was looked at, and why it was not enough. */
export interface Refusal {
  reason: string;
  looked_in: string[];
}

/** GET /exceptions/{id} */
export interface EvidencePack {
  exception_id: string;
  exception_class: ExceptionClass;
  status: ExceptionStatus;
  vendor: string;
  invoice_id: string;
  facts: Fact[];
  proposed: ProposedDecision | null;
  refusal: Refusal | null;
}

/** GET /policies */
export interface Policy {
  id: string;
  version: number;
  condition: string;
  action: string;
  rationale: string;
  approved_by: string;
  approved_at: string;
  learned_from: string;
  cited_by: string[];
}

/** GET /metrics */
export interface Metrics {
  human_touches: number;
  auto_cleared: number;
  refused: number;
  evidence_items: number;
}

/** POST /exceptions/{id}/decide */
export interface DecideRequest {
  action: DecisionAction;
  by: string;
  note?: string;
}

export interface DecideResponse {
  exception_id: string;
  status: ExceptionStatus;
  policy: Policy;
}

/** GET /exceptions/{id}/events — the SSE stream, one object per message. */
export type EngineEvent =
  | { type: "step"; at: string; label: string }
  | { type: "fact"; at: string; fact: Fact }
  | { type: "proposed"; at: string; proposed: ProposedDecision }
  | { type: "refused"; at: string; refusal: Refusal }
  | { type: "done"; at: string; status: ExceptionStatus };
