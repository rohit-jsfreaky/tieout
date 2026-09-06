import { Sparkle } from "@phosphor-icons/react";

import type { Decision } from "@/lib/api-types";
import { actionLabel, day, money } from "@/lib/format";
import type { Approver } from "@/lib/useDesk";

import { AuthorityNote } from "./AuthorityNote";
import { ChecklistLines } from "./ChecklistLines";
import { ConfidenceBar } from "./ConfidenceBar";

/**
 * What Tieout wants to do, or what has already been done.
 *
 * Four states share one card, because they are the same object: the proposal
 * waiting for a person, the auto-clear that cited a learned rule, the decision a
 * person actually recorded, and the one the authority matrix would not let them
 * make.
 */
export function DecisionCard({
  decision,
  approver,
  approverLimit,
}: {
  decision: Decision;
  approver: Approver;
  approverLimit: number | null;
}) {
  const blocked = decision.action === "escalate";
  const settled = decision.approved_by !== null && !blocked;
  return (
    <section className="surface rounded-lg bg-white p-4">
      <header className="flex items-baseline justify-between gap-3">
        <span className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          {blocked
            ? "Above their authority — escalated"
            : decision.auto
              ? "Cleared by a learned rule"
              : settled
                ? "Decision recorded"
                : "Proposed decision"}
        </span>
        <span className="text-faint font-mono text-[11px]">
          {actionLabel(decision.action)}
        </span>
      </header>

      <p className="mt-2 text-[14px] leading-relaxed font-medium">
        {decision.summary}
      </p>

      {decision.amount_payable !== null ? (
        <p className="text-muted mt-1 font-mono text-[12px]">
          pay {money(decision.amount_payable)}
        </p>
      ) : null}
      {decision.attach_po !== null ? (
        <p className="text-muted mt-1 font-mono text-[12px]">
          attach {decision.attach_po}
        </p>
      ) : null}

      <AuthorityNote
        decision={decision}
        approver={approver}
        approverLimit={approverLimit}
      />

      {decision.auto && decision.cited_policy ? (
        <p className="text-ledger mt-3 flex items-start gap-2 text-[13px] leading-relaxed font-medium">
          <Sparkle size={14} weight="fill" className="mt-[3px] shrink-0" aria-hidden />
          <span>
            {decision.cited_policy} — approved by {decision.approved_by}. No human
            needed.
          </span>
        </p>
      ) : null}

      {!decision.auto && (settled || blocked) ? (
        <p className="text-muted mt-3 text-[12px]">
          {decision.approved_by} · {day(decision.decided_at)}
          {decision.note ? ` · “${decision.note}”` : ""}
        </p>
      ) : null}

      <div className="mt-4">
        <ConfidenceBar value={decision.confidence} />
      </div>

      <ChecklistLines checks={decision.checks} />

      <p className="text-faint mt-4 border-t border-black/6 pt-3 text-[12px] leading-relaxed">
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
    </section>
  );
}
