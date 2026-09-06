import { ArrowFatLineUp } from "@phosphor-icons/react";

import type { Decision } from "@/lib/api-types";
import { limitLabel, money } from "@/lib/format";
import type { Approver } from "@/lib/useDesk";

/**
 * What signing this off would authorise, and whether the person at the desk is
 * allowed to do it.
 *
 * Both numbers came off the wire: `amount_for_authority` is published by the
 * engine on every decision, and the limit is the row for this seat in the matrix
 * `GET /authority` returned. The comparison here only decides what to *say* —
 * the engine blocks the approval server-side whatever this screen believes.
 */
export function AuthorityNote({
  decision,
  approver,
  approverLimit,
}: {
  decision: Decision;
  approver: Approver;
  /** `null` means no limit, or that the matrix has not landed yet. Warn on neither. */
  approverLimit: number | null;
}) {
  const amount = decision.amount_for_authority;
  if (amount === null || decision.authority_needed === null) return null;

  const above = approverLimit !== null && amount > approverLimit;

  return (
    <div
      className={`mt-3 rounded-md px-3 py-2.5 ${
        above ? "bg-ink/6" : "bg-soft"
      }`}
    >
      <p className="flex items-start gap-2 text-[12px] leading-relaxed">
        {above ? (
          <ArrowFatLineUp
            size={13}
            weight="fill"
            className="mt-[3px] shrink-0"
            aria-hidden
          />
        ) : null}
        <span>
          {above ? (
            <>
              <span className="font-medium">
                {money(amount)} is above your {limitLabel(approverLimit)} limit
                as {approver.role}. This needs the {decision.authority_needed}.
              </span>{" "}
              <span className="text-faint">
                Approving from this seat will be blocked and recorded.
              </span>
            </>
          ) : (
            <span className="text-muted">
              Authorises {money(amount)} for payment —{" "}
              {decision.authority_needed} authority. You are a {approver.role}
              {approverLimit === null ? "" : `, limit ${money(approverLimit)}`}.
            </span>
          )}
        </span>
      </p>
    </div>
  );
}
