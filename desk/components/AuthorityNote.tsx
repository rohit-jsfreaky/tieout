import { ArrowFatLineUp } from "@phosphor-icons/react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { AuthorityRow, Decision } from "@/lib/api-types";
import { money, roleArticle } from "@/lib/format";
import type { Approver } from "@/lib/useDesk";

/**
 * What signing this off would authorise, and whether the person at the desk is
 * allowed to do it.
 *
 * Both numbers came off the wire: `amount_for_authority` is published by the
 * engine on every decision, and the limit is this seat's row in the matrix
 * `GET /authority` returned. The comparison here only decides what to *say* —
 * `investigate.apply_human_decision` blocks the approval server-side whatever
 * this screen believes, and records the attempt as an escalation.
 */
export function AuthorityNote({
  decision,
  approver,
  seat,
}: {
  decision: Decision;
  approver: Approver;
  /** The approver's row in the matrix, or `null` while it is still in the air. */
  seat: AuthorityRow | null;
}) {
  const amount = decision.amount_for_authority;
  const needed = decision.authority_needed;
  if (amount === null || needed === null) return null;

  const limit = seat?.limit ?? null;
  const above = seat !== null && limit !== null && amount > limit;

  if (above) {
    // A decision that has already been recorded was signed by a seat that could
    // sign it, so the warning would be a lie. Say what actually happened instead.
    const recorded =
      decision.approved_by !== null && decision.action !== "escalate";
    return (
      <Alert className="bg-mist border-ink/10">
        <ArrowFatLineUp weight="fill" aria-hidden />
        <AlertTitle className="leading-relaxed text-balance">
          {money(amount)} is above {roleArticle(approver.role)} {approver.role}
          &apos;s {money(limit)} limit. This needs the {needed}.
        </AlertTitle>
        <AlertDescription className="text-[12px] leading-relaxed">
          {recorded
            ? `Recorded by ${decision.approved_by}, who could sign it. This seat could not have.`
            : `Approving from this seat is blocked and recorded as an escalation. Change the seat to ${needed} and the same evidence pack goes through.`}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <p className="text-muted-foreground text-[12px] leading-relaxed">
      Authorises {money(amount)} for payment — {needed} authority.{" "}
      {seat === null
        ? `Your limit as ${roleArticle(approver.role)} ${approver.role} has not loaded yet.`
        : limit === null
          ? `As ${roleArticle(approver.role)} ${approver.role} you sign with no limit.`
          : `As ${roleArticle(approver.role)} ${approver.role} you may sign up to ${money(limit)}.`}
    </p>
  );
}

/**
 * Whether this decision is above the approver's limit — the one place that
 * comparison is written, so the alert and the disabled Approve button can never
 * disagree with each other.
 */
export function aboveAuthority(
  decision: Decision | null,
  seat: AuthorityRow | null,
): boolean {
  if (decision === null || seat === null || seat.limit === null) return false;
  return (
    decision.amount_for_authority !== null &&
    decision.amount_for_authority > seat.limit
  );
}
