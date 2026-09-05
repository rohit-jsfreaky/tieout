import type { PolicyRow } from "@/lib/api-types";

import { EmptyNote } from "./EmptyNote";
import { Panel } from "./Panel";
import { PolicyCard } from "./PolicyCard";

/** Learned rules, each stamped with the person who approved it and the date. */
export function PoliciesPanel({
  policies,
  learned,
}: {
  policies: PolicyRow[];
  /** The ref of the rule the last approval created, so it can announce itself. */
  learned: string | null;
}) {
  return (
    <Panel title="Policies" aside={policies.length ? `${policies.length}` : "—"}>
      {policies.length === 0 ? (
        <EmptyNote>
          No rules yet. The first one is born the moment a human approves a
          decision, and carries their name.
        </EmptyNote>
      ) : (
        <div className="space-y-2">
          {policies.map((row) => (
            <PolicyCard
              key={row.policy.ref}
              row={row}
              fresh={row.policy.ref === learned}
            />
          ))}
        </div>
      )}
    </Panel>
  );
}
