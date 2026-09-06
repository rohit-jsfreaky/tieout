import type { QueueRow } from "@/lib/api-types";
import { money } from "@/lib/format";
import { deskMoney } from "@/lib/totals";

import { Figure } from "./Figure";

/**
 * The four sums a finance person asks for first: what was billed, what is being
 * held back, what cleared itself, and what is still on somebody's desk.
 *
 * This is a finance product, so the money leads and the counts follow. Every
 * figure is added up in `lib/totals.ts` out of amounts the API published —
 * nothing on this strip is invented, and nothing is a rate.
 */
export function MoneyStrip({
  queue,
  loading,
}: {
  queue: QueueRow[];
  loading: boolean;
}) {
  const total = deskMoney(queue);
  const figure = (amount: number) =>
    loading ? undefined : money(amount, total.currency);
  const count = (rows: number, one: string, many: string) =>
    `${rows} ${rows === 1 ? one : many}`;

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
      <Figure
        label="Billed"
        value={figure(total.billed)}
        hint={count(queue.length, "invoice that broke", "invoices that broke")}
        lead
        loading={loading}
      />
      <Figure
        label="Held back"
        value={figure(total.held)}
        hint="billed, minus what the order and the goods receipt support"
        lead
        loading={loading}
      />
      <Figure
        label="Auto-approved for payment"
        value={figure(total.autoApproved)}
        hint={`${count(total.autoCount, "invoice", "invoices")} cleared by a learned rule — nobody was asked`}
        lead
        ledger
        loading={loading}
      />
      <Figure
        label="Waiting on a person"
        value={figure(total.waiting)}
        hint={count(
          total.waitingCount,
          "invoice needs a decision",
          "invoices need a decision",
        )}
        lead
        loading={loading}
      />
    </div>
  );
}
