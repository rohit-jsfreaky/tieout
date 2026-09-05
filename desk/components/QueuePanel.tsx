import type { QueueRow } from "@/lib/api-types";

import { EmptyNote } from "./EmptyNote";
import { Panel } from "./Panel";
import { QueueRowCard } from "./QueueRowCard";

/** The exceptions, and nothing else. The clean 87% of invoices never appear here. */
export function QueuePanel({
  queue,
  selectedId,
  runningId,
  loading,
  onSelect,
}: {
  queue: QueueRow[];
  selectedId: string | null;
  runningId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <Panel title="Queue" aside={queue.length ? `${queue.length}` : "—"}>
      {queue.length === 0 ? (
        <EmptyNote>
          {loading
            ? "Matching every open invoice against its order and its goods receipt…"
            : "Nothing broke. Clean invoices never reach this desk."}
        </EmptyNote>
      ) : (
        <div className="-mx-2 space-y-1">
          {queue.map((row) => (
            <QueueRowCard
              key={row.exception.id}
              row={row}
              selected={row.exception.id === selectedId}
              running={row.exception.id === runningId || row.running}
              onSelect={() => onSelect(row.exception.id)}
            />
          ))}
        </div>
      )}
    </Panel>
  );
}
