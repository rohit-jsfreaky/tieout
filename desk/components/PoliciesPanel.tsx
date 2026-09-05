import { EmptyNote } from "./EmptyNote";
import { Panel } from "./Panel";

/** Learned rules, each stamped with the person who approved it and the date. */
export function PoliciesPanel() {
  return (
    <Panel title="Policies" aside="—">
      <EmptyNote>
        No rules yet. The first one is born the moment a human approves a
        decision, and carries their name.
      </EmptyNote>
    </Panel>
  );
}
