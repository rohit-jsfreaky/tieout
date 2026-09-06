import type { Metrics } from "@/lib/api-types";

import { Figure } from "./Figure";

/**
 * Seven counts, all counted from the store on every request.
 *
 * These sit UNDER the money, because a controller reads the money first and the
 * actions second. Human touches is still the one that has to fall: five
 * exceptions, one approval, and the rest clear themselves. "Still open" is its
 * honest counterweight — the exceptions nobody has picked up yet, so the strip
 * never lets three worked stand in for five found. Nothing here is typed in, and
 * a counter reads "—" until a real run has supplied it.
 */
export function CounterStrip({
  metrics,
  loading,
}: {
  metrics: Metrics | null;
  loading: boolean;
}) {
  const count = (value: number | undefined) =>
    value === undefined ? undefined : String(value);

  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-7">
      <Figure
        label="Exceptions"
        value={count(metrics?.exceptions_found)}
        loading={loading}
      />
      <Figure
        label="Still open"
        value={count(metrics?.open_not_worked)}
        loading={loading}
      />
      <Figure
        label="Human touches"
        value={count(metrics?.human_touches)}
        loading={loading}
        ledger
      />
      <Figure
        label="Auto-cleared"
        value={count(metrics?.auto_cleared)}
        loading={loading}
      />
      <Figure
        label="Refused"
        value={count(metrics?.refused)}
        loading={loading}
      />
      <Figure
        label="Evidence items"
        value={count(metrics?.evidence_items)}
        loading={loading}
      />
      <Figure
        label="Screenshots"
        value={count(metrics?.screenshots)}
        loading={loading}
      />
    </div>
  );
}
