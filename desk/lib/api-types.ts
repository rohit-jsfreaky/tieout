/**
 * The shapes the API sends, mirrored by hand from the backend.
 *
 * Every interesting one is an ENGINE model — `backend/src/tieout/engine/models.py`
 * and `events.py` — because `api/schemas.py` re-exports them unchanged and adds
 * nothing of its own except the wrappers at the bottom of this file. Keep the two
 * files in the same order so a reader can hold them side by side.
 *
 * Pydantic `computed_field`s (qty_short, exposure, ref, …) are serialised too, so
 * the desk never recomputes a number the engine already published.
 */

/* ------------------------------------------------------------------ vocabulary */

/** The three places Tieout is allowed to look. */
export type Source = "erp" | "inbox" | "portal";

export type FactKind =
  | "invoice"
  | "purchase_order"
  | "goods_receipt"
  | "candidate_purchase_order"
  | "vendor_email"
  | "delivery_note"
  | "portal_absence";

export type ExceptionKind =
  | "short_ship"
  | "price_variance"
  | "missing_po"
  | "unknown";

export type DecisionAction =
  | "short_pay"
  | "approve"
  | "attach_po"
  | "reject"
  | "refuse";

export type ExceptionStatus =
  | "open"
  | "proposed"
  | "refused"
  | "auto_cleared"
  | "resolved";

/* ------------------------------------------------------------- the exception */

export interface LineDiscrepancy {
  line_no: number;
  sku: string;
  description: string;
  qty_billed: number;
  qty_received: number | null;
  qty_ordered: number | null;
  unit_price_billed: number;
  unit_price_ordered: number | null;
  qty_short: number;
  price_delta: number;
  price_delta_pct: number;
  overbilled: number;
}

/** An invoice that did not tie out, and the numbers that prove it. */
export interface ExceptionCase {
  id: string;
  invoice_id: string;
  vendor_id: string;
  vendor_name: string;
  po_id: string | null;
  kind: ExceptionKind;
  headline: string;
  amount: number;
  currency: string;
  invoice_date: string;
  detected_at: string;
  status: ExceptionStatus;
  lines: LineDiscrepancy[];
  qty_billed: number;
  qty_received: number;
  qty_short: number;
  short_pct: number;
  price_variance_pct: number;
  /** The money at stake: billed, minus what the order and the receipt support. */
  exposure: number;
  supported_amount: number;
}

/* ------------------------------------------------------------ the audit trail */

export interface Figures {
  qty_ordered: number | null;
  qty_shipped: number | null;
  qty_received: number | null;
  qty_billed: number | null;
  unit_price: number | null;
  amount: number | null;
  event_date: string | null;
}

/** Something Tieout observed. Written only by `evidence.py`. */
export interface Fact {
  id: string;
  exception_id: string;
  source: Source;
  kind: FactKind;
  statement: string;
  locator: string;
  observed_at: string;
  raw: string;
  figures: Figures;
  /** An absolute path on the engine's machine; served by `GET /screenshots/{name}`. */
  screenshot: string | null;
  /** `"code"`, or the model id that read it out of prose. */
  extracted_by: string;
}

/** Somewhere Tieout looked — including the places that held nothing. */
export interface LookupStep {
  source: Source;
  action: string;
  locator: string;
  found: boolean;
  at: string;
  note: string;
}

/** One line of a class's deterministic checklist. The checklist IS the confidence. */
export interface Check {
  name: string;
  passed: boolean;
  weight: number;
  detail: string;
}

/** What Tieout proposes, or what actually happened. Never written by the model. */
export interface Decision {
  exception_id: string;
  action: DecisionAction;
  summary: string;
  rationale: string;
  rationale_by: string;
  confidence: number;
  checks: Check[];
  /** True when a learned rule cleared this without a person. */
  auto: boolean;
  cited_policy: string | null;
  approved_by: string | null;
  decided_at: string;
  amount_payable: number | null;
  attach_po: string | null;
  note: string;
}

export interface EvidencePack {
  exception: ExceptionCase;
  facts: Fact[];
  steps: LookupStep[];
  started_at: string;
  finished_at: string | null;
  proposal: Decision | null;
  sources_used: Source[];
}

/* -------------------------------------------------------------------- the rule */

export interface PolicyCondition {
  kind: ExceptionKind;
  vendor_id: string | null;
  vendor_name: string | null;
  max_short_pct: number | null;
  max_price_variance_pct: number | null;
  max_exposure: number | null;
  requires: FactKind[];
}

/** A rule Tieout learned from one human decision, with that human's name on it. */
export interface Policy {
  id: string;
  version: number;
  name: string;
  kind: ExceptionKind;
  condition: PolicyCondition;
  action: DecisionAction;
  rationale: string;
  drafted_by: string;
  approved_by: string;
  approved_at: string;
  learned_from: string;
  learned_from_invoice: string;
  active: boolean;
  superseded_at: string | null;
  supersedes_version: number | null;
  /** `SHORT-SHIP-01 v1` — what a decision cites. */
  ref: string;
}

export interface Metrics {
  exceptions_found: number;
  worked: number;
  auto_cleared: number;
  refused: number;
  awaiting_human: number;
  human_touches: number;
  touches_avoided_by_policy: number;
  evidence_items: number;
  screenshots: number;
  policies_active: number;
  policy_citations: number;
}

/* ------------------------------------------------------ the API's own wrappers */

/** GET /queue */
export interface QueueRow {
  exception: ExceptionCase;
  decision: Decision | null;
  facts: number;
  running: boolean;
}

export interface QueueResponse {
  count: number;
  exceptions: QueueRow[];
}

/** GET /exceptions/{id} */
export interface ExceptionDetail {
  exception: ExceptionCase;
  pack: EvidencePack | null;
  decision: Decision | null;
  policy: Policy | null;
  running: boolean;
  events: string;
}

/** POST /exceptions/{id}/work */
export interface WorkAccepted {
  exception_id: string;
  state: string;
  events: string;
}

/** What a person is allowed to do. `approve` means "do what Tieout proposed". */
export type DecidableAction = "approve" | "reject" | "short_pay" | "attach_po";

export interface DecideRequest {
  action: DecidableAction;
  by: string;
  note?: string;
}

/** POST /exceptions/{id}/decide */
export interface DecideResponse {
  exception: ExceptionCase;
  decision: Decision;
  policy: Policy | null;
}

/** GET /policies */
export interface PolicyRow {
  policy: Policy;
  cited_by: string[];
}

export interface PoliciesResponse {
  count: number;
  policies: PolicyRow[];
}

/** POST /reset */
export interface ResetResponse {
  message: string;
  world: Record<string, unknown>;
}

/* ------------------------------------------------------------------ the stream */

export type EventKind =
  | "matched"
  | "investigating"
  | "step"
  | "fact"
  | "enough"
  | "proposed"
  | "refused"
  | "auto_cleared"
  | "decided"
  | "policy_learned"
  | "policy_versioned"
  | "warning";

export const EVENT_KINDS: EventKind[] = [
  "matched",
  "investigating",
  "step",
  "fact",
  "enough",
  "proposed",
  "refused",
  "auto_cleared",
  "decided",
  "policy_learned",
  "policy_versioned",
  "warning",
];

/** One `engine.events.Event`, forwarded over SSE unchanged. */
export interface EngineEvent {
  kind: EventKind;
  message: string;
  at: string;
  exception_id: string | null;
  fact: Fact | null;
  step: LookupStep | null;
  decision: Decision | null;
  policy: Policy | null;
}

/** The only shape on the wire the engine did not write: transport, not evidence. */
export interface DoneEvent {
  exception_id: string;
  state: "idle" | "running" | "done" | "failed";
  error: string;
}
