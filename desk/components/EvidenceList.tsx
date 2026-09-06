import type { Fact, Source } from "@/lib/api-types";

import { FactRow } from "./FactRow";
import { SourceChip } from "./SourceChip";

/**
 * The trail, in the order it was walked.
 *
 * Tieout reads one source at a time, so consecutive facts from the same source
 * are one visit and are drawn as one: "Inbox · 3 facts" with three lines under
 * it, rather than three identical boxes each announcing where it came from. The
 * grouping is only ever over neighbours — if the agent goes back to the ERP
 * after the portal, that is a second visit and gets its own heading, because the
 * order is part of the evidence.
 */
export function EvidenceList({
  facts,
  onShowScreenshot,
}: {
  facts: Fact[];
  onShowScreenshot?: (fact: Fact) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      {groupBySource(facts).map((visit) => (
        <section key={visit.key} className="flex flex-col gap-1">
          <header className="flex items-center gap-2 px-2">
            <SourceChip source={visit.source} />
            <span className="text-faint font-mono text-[11px]">
              {visit.facts.length} {visit.facts.length === 1 ? "fact" : "facts"}
            </span>
          </header>
          <ul className="border-border/70 ml-[9px] flex flex-col border-l pl-1">
            {visit.facts.map((fact) => (
              <FactRow
                key={fact.id}
                fact={fact}
                onShowScreenshot={onShowScreenshot}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

interface Visit {
  key: string;
  source: Source;
  facts: Fact[];
}

/** Runs of neighbours, never a re-sort: the order facts landed in is evidence. */
function groupBySource(facts: Fact[]): Visit[] {
  const visits: Visit[] = [];
  for (const fact of facts) {
    const last = visits[visits.length - 1];
    if (last && last.source === fact.source) last.facts.push(fact);
    else visits.push({ key: fact.id, source: fact.source, facts: [fact] });
  }
  return visits;
}
