import { HandPalm } from "@phosphor-icons/react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Decision, LookupStep } from "@/lib/api-types";
import { clock } from "@/lib/format";

import { ChecklistLines } from "./ChecklistLines";
import { ConfidenceBar } from "./ConfidenceBar";
import { SourceChip } from "./SourceChip";
import { WhyThisDecision } from "./WhyThisDecision";

/**
 * Refusing is an outcome, not an error.
 *
 * So it gets the same card as a decision — same size, same order, no badge of
 * its own, because the header at the top of the view has already said where
 * this exception stands — plus the thing that makes it trustworthy: every place
 * Tieout looked, including the ones that held nothing.
 */
export function RefusalCard({
  decision,
  steps,
}: {
  decision: Decision;
  steps: LookupStep[];
}) {
  return (
    <Card className="[--card-spacing:--spacing(5)]">
      <CardHeader>
        <CardTitle className="text-faint flex items-center gap-2 text-[11px] font-medium tracking-[0.1em] uppercase">
          <HandPalm size={15} weight="bold" aria-hidden />
          Not confident — you decide
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <p className="font-display text-[19px] leading-snug font-[450]">
          {decision.summary}
        </p>

        <div className="flex flex-col gap-3">
          <ConfidenceBar value={decision.confidence} tone="quiet" />
          <ChecklistLines checks={decision.checks} />
        </div>

        <Separator />

        <div className="flex flex-col gap-2">
          <p className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
            Here is where I looked ({steps.length})
          </p>
          <ul className="flex flex-col gap-1.5">
            {steps.map((step) => (
              <li
                key={`${step.source}|${step.action}|${step.locator}|${step.at}`}
                className="flex items-start gap-2 text-[12px]"
              >
                <SourceChip source={step.source} />
                <span className="min-w-0 flex-1">
                  <span
                    className={step.found ? "text-muted-foreground" : "text-faint"}
                  >
                    {step.action}
                  </span>
                  <span className="text-faint block truncate font-mono text-[11px]">
                    {step.locator}
                  </span>
                  {step.note ? (
                    <span className="text-faint block text-[11px]">
                      {step.note}
                    </span>
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

        <Separator />

        <WhyThisDecision
          rationale={decision.rationale}
          writtenBy={decision.rationale_by}
          defaultOpen
        />
      </CardContent>
    </Card>
  );
}
