import { HandPalm } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
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

/**
 * Refusing is an outcome, not an error.
 *
 * So it gets the same card as a decision, plus the thing that makes it
 * trustworthy: every place Tieout looked, including the ones that held nothing.
 */
export function RefusalCard({
  decision,
  steps,
}: {
  decision: Decision;
  steps: LookupStep[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-[11px] font-medium tracking-[0.1em] uppercase">
          <HandPalm size={15} weight="bold" aria-hidden />
          Not confident — you decide
        </CardTitle>
        <CardAction>
          <Badge variant="outline">Refused</Badge>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <p className="text-[14px] leading-relaxed font-medium">
          {decision.summary}
        </p>

        <ConfidenceBar value={decision.confidence} tone="quiet" />
        <ChecklistLines checks={decision.checks} />

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

        <p className="text-faint text-[12px] leading-relaxed">
          {decision.rationale}
        </p>
      </CardContent>
    </Card>
  );
}
