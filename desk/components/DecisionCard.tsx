import { Sparkle } from "@phosphor-icons/react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Decision } from "@/lib/api-types";
import { actionLabel, day, money } from "@/lib/format";

import { ChecklistLines } from "./ChecklistLines";
import { ConfidenceBar } from "./ConfidenceBar";
import { Figure, FigureRow } from "./FigureRow";
import { WhyThisDecision } from "./WhyThisDecision";

/**
 * What Tieout wants to do, or what has already been done.
 *
 * The most important thing on the view, so it is the biggest: the sentence in
 * the display face, everything else beneath it. Four states share one card,
 * because they are the same object: the proposal waiting for a person, the
 * auto-clear that cited a learned rule, the decision a person actually recorded
 * — and the one they were not allowed to record, which is an outcome with a
 * name on it rather than an error.
 *
 * There is no badge here. The status of the exception is stated once, in the
 * header at the top of the view; the action is a named figure like the others,
 * because "Short-pay" is what Tieout wants to DO, not where the invoice stands.
 */
export function DecisionCard({ decision }: { decision: Decision }) {
  const escalated = decision.action === "escalate";
  const settled = decision.approved_by !== null;
  return (
    <Card className="[--card-spacing:--spacing(5)]">
      <CardHeader>
        <CardTitle className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          {decision.auto
            ? "Cleared by a learned rule"
            : escalated
              ? "Above their authority — escalated"
              : settled
                ? "Decision recorded"
                : "Proposed decision"}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <p className="font-display text-[19px] leading-snug font-[450]">
            {decision.summary}
          </p>
          <FigureRow>
            <Figure label="action" value={actionLabel(decision.action)} />
            {decision.amount_payable !== null ? (
              <Figure label="pay" value={money(decision.amount_payable)} />
            ) : null}
            {decision.attach_po !== null ? (
              <Figure label="attach" value={decision.attach_po} />
            ) : null}
          </FigureRow>
        </div>

        {decision.auto && decision.cited_policy ? (
          <p className="text-ledger flex items-start gap-2 text-[13px] leading-relaxed font-medium">
            <Sparkle size={14} weight="fill" className="mt-[3px] shrink-0" aria-hidden />
            <span>
              {decision.cited_policy} — approved by {decision.approved_by}. No
              human needed.
            </span>
          </p>
        ) : null}

        {!decision.auto && settled ? (
          <p className="text-muted-foreground text-[12px]">
            {escalated
              ? `${decision.approved_by} tried to sign this`
              : decision.approved_by}{" "}
            · {day(decision.decided_at)}
            {decision.note ? ` · “${decision.note}”` : ""}
          </p>
        ) : null}

        <div className="flex flex-col gap-3">
          <ConfidenceBar value={decision.confidence} />
          <ChecklistLines checks={decision.checks} />
        </div>

        <Separator />

        <WhyThisDecision
          key={decision.auto ? "auto" : "human"}
          rationale={decision.rationale}
          writtenBy={decision.rationale_by}
          defaultOpen={!decision.auto}
        />
      </CardContent>
    </Card>
  );
}
