import { EmptyNote } from "./EmptyNote";
import { Panel } from "./Panel";

/** The exception queue. Rows arrive in 4b; the row that matters reads
 *  "cleared by SHORT-SHIP-01 · Chris, Controller". */
export function QueuePanel() {
  return (
    <Panel title="Queue" aside="—">
      <EmptyNote>
        Exceptions appear here after a reset. Clean invoices never do.
      </EmptyNote>
    </Panel>
  );
}
