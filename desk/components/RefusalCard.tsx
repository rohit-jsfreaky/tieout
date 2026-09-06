import { HandPalm } from "@phosphor-icons/react";

import type { Decision, LookupStep } from "@/lib/api-types";
import { clock } from "@/lib/format";
import type { Approver } from "@/lib/useDesk";

import { AuthorityNote } from "./AuthorityNote";
import { ChecklistLines } from "./ChecklistLines";
import { ConfidenceBar } from "./ConfidenceBar";
import { SourceChip } from "./SourceChip";

/**
 * Refusing is an outcome, not an error.
 *
 * So it gets the same card as a decision, plus the thing that makes it
 * trustworthy: every place Tieout looked, including the ones that held nothing.
 */
export function RefusalCard({
  decision,
  steps,
  approver,
  approverLimit,
}: {
  decision: Decision;
  steps: LookupStep[];
  approver: Approver;
  approverLimit: number | null;
}) {
  return (
    <section className="surface rounded-lg bg-white p-4">
      <header className="flex items-center gap-2">
        <HandPalm size={15} weight="bold" aria-hidden />
        <span className="text-[11px] font-medium tracking-[0.1em] uppercase">
          Not confident — you decide
        </span>
      </header>

      <p className="mt-2 text-[14px] leading-relaxed font-medium">
        {decision.summary}
      </p>

      {/* Two independent reasons this cannot end here: Tieout is not confident,
          AND paying it may be above the authority of whoever is at the desk. */}
      <AuthorityNote
        decision={decision}
        approver={approver}
        approverLimit={approverLimit}
      />

      <div className="mt-4">
        <ConfidenceBar value={decision.confidence} tone="quiet" />
      </div>

      <ChecklistLines checks={decision.checks} />

      <div className="mt-4 border-t border-black/6 pt-3">
        <p className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          Here is where I looked ({steps.length})
        </p>
        <ul className="mt-2 space-y-1.5">
          {steps.map((step) => (
            <li
              key={`${step.source}|${step.action}|${step.locator}|${step.at}`}
              className="flex items-start gap-2 text-[12px]"
            >
              <SourceChip source={step.source} size={11} />
              <span className="min-w-0 flex-1">
                <span className={step.found ? "text-muted" : "text-faint"}>
                  {step.action}
                </span>
                <span className="text-faint block truncate font-mono text-[11px]">
                  {step.locator}
                </span>
                {step.note ? (
                  <span className="text-faint block text-[11px]">{step.note}</span>
                ) : null}
              </span>
              <span
                className={`shrink-0 font-mono text-[11px] ${
                  step.found ? "text-ledger" : "text-faint"
                }`}
              >
                {step.found ? "found" : "nothing"}
              </span>
              <span className="text-faint shrink-0 font-mono text-[11px]">
                {clock(step.at)}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-faint mt-4 border-t border-black/6 pt-3 text-[12px] leading-relaxed">
        {decision.rationale}
      </p>
    </section>
  );
}
