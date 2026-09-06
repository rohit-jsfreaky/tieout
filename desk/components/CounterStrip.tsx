import type { Metrics } from "@/lib/api-types";

import { Counter } from "./Counter";

/**
 * Six figures, all counted from the store on every request.
 *
 * Human touches is the one that has to fall: five exceptions, one approval, and
 * the rest clear themselves. Nothing here is typed in, and a counter reads "—"
 * until a real run has supplied it.
 */
export function CounterStrip({
  metrics,
  loading,
}: {
  metrics: Metrics | null;
  loading: boolean;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
      <Counter
        label="Exceptions"
        value={metrics?.exceptions_found}
        loading={loading}
      />
      <Counter
        label="Human touches"
        value={metrics?.human_touches}
        loading={loading}
        winning
      />
      <Counter
        label="Auto-cleared"
        value={metrics?.auto_cleared}
        loading={loading}
      />
      <Counter label="Refused" value={metrics?.refused} loading={loading} />
      <Counter
        label="Evidence items"
        value={metrics?.evidence_items}
        loading={loading}
      />
      <Counter
        label="Screenshots"
        value={metrics?.screenshots}
        loading={loading}
      />
    </div>
  );
}
