import { Sparkle } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Decision } from "@/lib/api-types";
import { actionLabel, day, money } from "@/lib/format";

import { ChecklistLines } from "./ChecklistLines";
import { ConfidenceBar } from "./ConfidenceBar";

/**
 * What Tieout wants to do, or what has already been done.
 *
 * Four states share one card, because they are the same object: the proposal
 * waiting for a person, the auto-clear that cited a learned rule, the decision a
 * person actually recorded — and the one they were not allowed to record, which
 * is an outcome with a name on it rather than an error.
 */
export function DecisionCard({ decision }: { decision: Decision }) {
  const escalated = decision.action === "escalate";
  const settled = decision.approved_by !== null;
  return (
    <Card>
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
        <CardAction>
          <Badge variant={decision.auto ? "ledger" : "secondary"}>
            {actionLabel(decision.action)}
          </Badge>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-[14px] leading-relaxed font-medium">
            {decision.summary}
          </p>
          {decision.amount_payable !== null ? (
            <p className="text-muted-foreground font-mono text-[12px]">
              pay {money(decision.amount_payable)}
            </p>
          ) : null}
          {decision.attach_po !== null ? (
            <p className="text-muted-foreground font-mono text-[12px]">
              attach {decision.attach_po}
            </p>
          ) : null}
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

        <ConfidenceBar value={decision.confidence} />
        <ChecklistLines checks={decision.checks} />

        <Separator />

        <p className="text-faint text-[12px] leading-relaxed">
          {decision.rationale}
          <span className="font-mono">
            {" "}
            ({decision.rationale_by === "code"
              ? "written by code"
              : decision.rationale_by === "human"
                ? "written by hand"
                : `written by ${decision.rationale_by}`}
            )
          </span>
        </p>
      </CardContent>
    </Card>
  );
}
