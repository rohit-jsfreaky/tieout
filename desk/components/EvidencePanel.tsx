import { EmptyNote } from "./EmptyNote";
import { Panel } from "./Panel";

/** The evidence pack: facts as they land, each with its source, the time and a
 *  portal screenshot, then the proposed decision — or the refusal. */
export function EvidencePanel() {
  return (
    <Panel title="Evidence pack" aside="—">
      <div className="flex h-full flex-col gap-6">
        <EmptyNote>
          Pick an exception and press Work. Every fact lands here with where it
          came from, when it was read, and a screenshot if it came from the
          vendor portal.
        </EmptyNote>

        {/* The proposed decision sits at the foot of the pack, above the
            buttons, with its confidence drawn as a recessed track. */}
        <div className="mt-auto">
          <div className="surface rounded-lg bg-white p-4">
            <div className="flex items-baseline justify-between">
              <span className="text-muted text-[13px]">Proposed decision</span>
              <span className="text-faint font-mono text-[11px]">
                confidence —
              </span>
            </div>
            <div className="well mt-3 h-1.5 rounded-xs bg-mist" />
          </div>
        </div>
      </div>
    </Panel>
  );
}
