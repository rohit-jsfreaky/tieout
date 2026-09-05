import type { Metrics } from "@/lib/api-types";

import { Counter } from "./Counter";

/**
 * Six figures, all counted from the store on every request.
 *
 * Human touches is the one that has to fall: five exceptions, one approval, and
 * the rest clear themselves. Nothing here is typed in, and a counter reads "—"
 * until a real run has supplied it.
 */
export function CounterStrip({ metrics }: { metrics: Metrics | null }) {
  const figure = (value: number | undefined) =>
    value === undefined ? null : String(value);

  return (
    <div className="well flex gap-1 rounded-lg bg-soft p-1">
      <Counter label="Exceptions" value={figure(metrics?.exceptions_found)} />
      <Counter label="Human touches" value={figure(metrics?.human_touches)} winning />
      <Counter label="Auto-cleared" value={figure(metrics?.auto_cleared)} />
      <Counter label="Refused" value={figure(metrics?.refused)} />
      <Counter label="Evidence items" value={figure(metrics?.evidence_items)} />
      <Counter label="Screenshots" value={figure(metrics?.screenshots)} />
    </div>
  );
}
