import { Stamp } from "@phosphor-icons/react";

import type { PolicyRow } from "@/lib/api-types";
import { actionLabel, day, exceptionKindLabel, factKindLabel, money } from "@/lib/format";

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
    <article
      className={`rounded-lg bg-white p-3.5 ${
        fresh ? "surface-raised animate-land" : "surface"
      } ${policy.active ? "" : "opacity-60"}`}
    >
      <header className="flex items-baseline gap-2">
        <span className="font-mono text-[12px] font-medium">{policy.id}</span>
        <span
          className={`font-mono text-[11px] ${
            policy.active ? "text-ledger" : "text-faint"
          }`}
        >
          v{policy.version}
        </span>
        <span className="text-faint ml-auto text-[11px]">
          {policy.active ? "active" : "superseded"}
        </span>
      </header>

      <h3 className="font-display mt-1 text-[15px] leading-snug font-[500]">
        {policy.name}
      </h3>

      <dl className="mt-3 space-y-2">
        <div>
          <dt className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
            When
          </dt>
          <dd className="text-muted mt-0.5 text-[12px] leading-relaxed">
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

      <p className="text-ledger mt-3 flex items-start gap-1.5 text-[12px] leading-snug font-medium">
        <Stamp size={13} weight="fill" className="mt-[2px] shrink-0" aria-hidden />
        <span>
          {policy.approved_by} · {day(policy.approved_at)}
        </span>
      </p>

      <p className="text-faint mt-2 font-mono text-[11px]">
        learned from {policy.learned_from} · {policy.learned_from_invoice}
        {policy.supersedes_version !== null
          ? ` · replaces v${policy.supersedes_version}`
          : ""}
      </p>

      <p className="mt-1 font-mono text-[11px]">
        <span className="text-faint">cited by </span>
        <span className={cited_by.length ? "text-ledger" : "text-faint"}>
          {cited_by.length ? cited_by.join(", ") : "nothing yet"}
        </span>
      </p>

      <p className="text-faint mt-3 border-t border-black/6 pt-2.5 text-[12px] leading-relaxed">
        {policy.rationale}
        <span className="font-mono">
          {" "}
          ({policy.drafted_by === "code"
            ? "drafted by code"
            : `drafted by ${policy.drafted_by}, clamped by code`}
          )
        </span>
      </p>
    </article>
  );
}

/**
 * The rule's "when", in the order `PolicyCondition.describe()` writes it.
 *
 * That method is a plain Python method, so it is not on the wire — but every
 * field it reads is, and this is a rendering of those fields, not a second
 * opinion about them.
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
  if (when.requires.length > 0) {
    lines.push(
      `evidence includes ${when.requires
        .map((kind) => factKindLabel(kind).toLowerCase())
        .join(", ")}`,
    );
  }
  return lines;
}
