import { CheckCircle, CircleNotch } from "@phosphor-icons/react";

import type { QueueRow } from "@/lib/api-types";
import { exceptionKindLabel, money, statusLabel } from "@/lib/format";

/**
 * One line of the queue.
 *
 * The last line of this card is the whole product: when a learned rule clears an
 * exception, the row says which rule and whose name is on it, and nobody had to
 * touch it.
 */
export function QueueRowCard({
  row,
  selected,
  running,
  onSelect,
}: {
  row: QueueRow;
  selected: boolean;
  running: boolean;
  onSelect: () => void;
}) {
  const { exception, decision } = row;
  const cleared = decision?.auto === true && decision.cited_policy !== null;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={selected}
      className={`block w-full rounded-md p-3 text-left transition-colors ${
        selected ? "surface bg-white" : "hover:bg-soft"
      }`}
    >
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[12px] font-medium">{exception.id}</span>
        <span className="text-muted text-[12px]">
          {exceptionKindLabel(exception.kind)}
        </span>
        <span className="ml-auto shrink-0">
          {running ? (
            <span className="text-ledger inline-flex items-center gap-1 text-[11px] font-medium">
              <CircleNotch size={11} weight="bold" className="animate-spin" aria-hidden />
              working
            </span>
          ) : (
            <span
              className={`text-[11px] font-medium ${
                exception.status === "auto_cleared" ? "text-ledger" : "text-faint"
              }`}
            >
              {statusLabel(exception.status)}
            </span>
          )}
        </span>
      </div>

      <div className="text-muted mt-1 truncate text-[12px]">
        {exception.invoice_id} · {exception.vendor_name}
      </div>

      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="font-mono text-[13px]">
          {money(exception.amount, exception.currency)}
        </span>
        <span className="text-faint font-mono text-[11px]">
          {money(exception.exposure, exception.currency)} at stake
        </span>
        {row.facts > 0 ? (
          <span className="text-faint ml-auto font-mono text-[11px]">
            {row.facts} facts
          </span>
        ) : null}
      </div>

      {cleared ? (
        <div className="animate-land mt-2 flex items-start gap-1.5 rounded-sm bg-ledger/8 px-2 py-1.5">
          <CheckCircle
            size={13}
            weight="fill"
            className="text-ledger mt-[2px] shrink-0"
            aria-hidden
          />
          <span className="text-ledger text-[12px] leading-snug font-medium">
            cleared by {decision?.cited_policy} · {decision?.approved_by}
          </span>
        </div>
      ) : null}
    </button>
  );
}
