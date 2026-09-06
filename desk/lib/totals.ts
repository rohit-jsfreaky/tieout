/**
 * The only file on the desk that adds two numbers together.
 *
 * Every term below is a field the API published on the row it belongs to — the
 * invoice total, the engine's `exposure`, the `amount_payable` a decision
 * authorised. The arithmetic is addition and nothing else: no rate, no
 * projection, no threshold. If a figure on this screen cannot be traced to a
 * number the engine sent, it does not belong here.
 */

import type { ExceptionStatus, PolicyRow, QueueRow } from "./api-types";

/**
 * Waiting on a person: proposed, refused, or above the approver's limit.
 *
 * The same three statuses `engine/metrics.py` counts for `awaiting_human` — an
 * escalation is waiting on a person too, just on a more senior one.
 */
const WAITING: ExceptionStatus[] = ["proposed", "refused", "escalated"];

/** Money is stored to the cent; adding floats is not. */
const cents = (amounts: number[]): number =>
  Math.round(amounts.reduce((total, amount) => total + amount, 0) * 100) / 100;

export interface DeskMoney {
  /** One buyer, one currency in this world — but it still comes off the rows. */
  currency: string;
  /** Everything the vendors billed on the invoices that broke. */
  billed: number;
  /** Billed, minus what the order and the goods receipt support. */
  held: number;
  /** What a learned rule approved for payment with nobody in the room. */
  autoApproved: number;
  autoCount: number;
  /** Still sitting on somebody's desk. */
  waiting: number;
  waitingCount: number;
}

export function deskMoney(queue: QueueRow[]): DeskMoney {
  const auto = queue.filter(
    (row) => row.decision?.auto === true && row.decision.amount_payable !== null,
  );
  const waiting = queue.filter((row) => WAITING.includes(row.exception.status));

  return {
    currency: queue[0]?.exception.currency ?? "USD",
    billed: cents(queue.map((row) => row.exception.amount)),
    held: cents(queue.map((row) => row.exception.exposure)),
    autoApproved: cents(auto.map((row) => row.decision?.amount_payable ?? 0)),
    autoCount: auto.length,
    waiting: cents(waiting.map((row) => row.exception.amount)),
    waitingCount: waiting.length,
  };
}

/**
 * The money one rule has approved for payment, from the auto-clears that cited
 * it. `null` when the rule has cleared nothing yet, so a column can read "—"
 * rather than a zero somebody has to interpret.
 */
export function clearedByRule(
  { cited_by }: PolicyRow,
  queue: QueueRow[],
): { amount: number; currency: string } | null {
  const cited = queue.filter(
    (row) =>
      cited_by.includes(row.exception.id) &&
      row.decision != null &&
      row.decision.amount_payable !== null,
  );
  if (cited.length === 0) return null;
  return {
    amount: cents(cited.map((row) => row.decision?.amount_payable ?? 0)),
    currency: cited[0].exception.currency,
  };
}
