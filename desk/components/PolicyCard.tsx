import { Stamp } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { PolicyRow } from "@/lib/api-types";
import {
  actionLabel,
  day,
  exceptionKindLabel,
  factKindLabel,
  limitLabel,
  money,
} from "@/lib/format";

/**
 * A rule Tieout learned from exactly one human decision.
 *
 * Everything on this card is on the rule itself: the version, the condition code
 * evaluates, the person who approved it, the day, the exception it came from and
 * the exceptions it has since cleared. That list is the self-improving loop, and
 * it is the reason a decision here can be audited a year from now.
 */
export function PolicyCard({ row, fresh }: { row: PolicyRow; fresh: boolean }) {
  const { policy, cited_by } = row;
  return (
    <Card
      className={`${fresh ? "surface-raised animate-land" : ""} ${
        policy.active ? "" : "opacity-60"
      }`}
    >
      <CardHeader>
        <CardTitle className="font-display text-[16px] font-[500]">
          {policy.name}
        </CardTitle>
        <CardDescription className="font-mono text-[12px]">
          {policy.id} · v{policy.version}
        </CardDescription>
        <CardAction>
          <Badge variant={policy.active ? "ledger" : "outline"}>
            {policy.active ? "active" : "superseded"}
          </Badge>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <dl className="flex flex-col gap-2">
          <div>
            <dt className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
              When
            </dt>
            <dd className="text-muted-foreground mt-0.5 text-[12px] leading-relaxed">
              {conditionLines(row).join("; ")}
            </dd>
          </div>
          <div>
            <dt className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
              Then
            </dt>
            <dd className="mt-0.5 text-[12px]">{actionLabel(policy.action)}</dd>
          </div>
        </dl>

        {/* The ceiling is inherited, not chosen: a rule may never clear more than
            the person who approved it could have cleared by hand. It sits next to
            their name because it is part of who signed this. */}
        <p className="text-ledger flex items-start gap-1.5 text-[12px] leading-snug font-medium">
          <Stamp size={13} weight="fill" className="mt-[2px] shrink-0" aria-hidden />
          <span>
            {policy.approved_by} (limit {limitLabel(policy.authority_ceiling)}) ·{" "}
            {day(policy.approved_at)}
          </span>
        </p>

        <div className="flex flex-col gap-1 font-mono text-[11px]">
          <p className="text-faint">
            learned from {policy.learned_from} · {policy.learned_from_invoice}
            {policy.supersedes_version !== null
              ? ` · replaces v${policy.supersedes_version}`
              : ""}
          </p>
          <p>
            <span className="text-faint">cited by </span>
            <span className={cited_by.length ? "text-ledger" : "text-faint"}>
              {cited_by.length ? cited_by.join(", ") : "nothing yet"}
            </span>
          </p>
        </div>

        <Separator />

        <p className="text-faint text-[12px] leading-relaxed">
          {policy.rationale}
          <span className="font-mono">
            {" "}
            ({policy.drafted_by === "code"
              ? "drafted by code"
              : `drafted by ${policy.drafted_by}, clamped by code`}
            )
          </span>
        </p>
      </CardContent>
    </Card>
  );
}

/**
 * The rule's "when", in the order `PolicyCondition.describe()` writes it, plus
 * the authority ceiling.
 *
 * That method is a plain Python method, so it is not on the wire — but every
 * field it reads is, and this is a rendering of those fields, not a second
 * opinion about them. The ceiling is not part of the condition — `policy.covers`
 * checks it separately — but it stops the rule exactly like the tolerances do,
 * so it is read here exactly like them.
 */
function conditionLines({ policy }: PolicyRow): string[] {
  const when = policy.condition;
  const lines = [`class is ${exceptionKindLabel(when.kind).toLowerCase()}`];
  if (when.vendor_id) {
    lines.push(`vendor is ${when.vendor_name ?? when.vendor_id}`);
  }
  if (when.max_short_pct !== null) {
    lines.push(`shortfall ≤ ${when.max_short_pct}% of the billed quantity`);
  }
  if (when.max_price_variance_pct !== null) {
    lines.push(`price variance ≤ ${when.max_price_variance_pct}%`);
  }
  if (when.max_exposure !== null) {
    lines.push(`exposure ≤ ${money(when.max_exposure)}`);
  }
  if (policy.authority_ceiling !== null) {
    lines.push(`payment ≤ ${money(policy.authority_ceiling)}`);
  }
  if (when.requires.length > 0) {
    lines.push(
      `evidence includes ${when.requires
        .map((kind) => factKindLabel(kind).toLowerCase())
        .join(", ")}`,
    );
  }
  return lines;
}
