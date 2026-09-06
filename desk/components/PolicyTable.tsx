"use client";

import { useState } from "react";

import { CaretDown, CaretRight, Stamp } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { PolicyRow, QueueRow } from "@/lib/api-types";
import {
  actionLabel,
  day,
  exceptionKindLabel,
  factKindLabel,
  limitLabel,
  money,
} from "@/lib/format";
import { clearedByRule } from "@/lib/totals";

/**
 * Every rule Tieout has learned, one line each.
 *
 * A line is a ledger entry: which rule, which version, whose approval created
 * it, what it has cleared since and how much money that was. Opening a line
 * shows the condition code actually evaluates, and the rationale written when
 * the rule was born. Nothing here is a summary of a rule — it is the rule, as
 * the engine published it.
 */
export function PolicyTable({
  rows,
  queue,
  fresh,
}: {
  rows: PolicyRow[];
  queue: QueueRow[];
  fresh: string | null;
}) {
  // The rule an approval just created opens itself, because that is the one the
  // person is looking for — and so does the first rule of all, because a policy
  // book with one line in it should show what that line says.
  const [open, setOpen] = useState<string | null>(
    fresh ?? (rows.length === 1 ? rows[0].policy.ref : null),
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-36">Rule</TableHead>
          <TableHead className="w-16">Version</TableHead>
          <TableHead>Name</TableHead>
          <TableHead className="w-28">Status</TableHead>
          <TableHead>Approved by</TableHead>
          <TableHead className="w-40">Learned from</TableHead>
          <TableHead className="w-16 text-right">Cited</TableHead>
          <TableHead className="w-36 text-right">Cleared</TableHead>
          <TableHead className="w-8" />
        </TableRow>
      </TableHeader>

      <TableBody>
        {rows.map((row) => {
          const { policy, cited_by } = row;
          const expanded = open === policy.ref;
          const cleared = clearedByRule(row, queue);

          return [
            <TableRow
              key={policy.ref}
              aria-expanded={expanded}
              onClick={() => setOpen(expanded ? null : policy.ref)}
              className={`cursor-pointer ${expanded ? "border-b-0" : ""} ${
                policy.active ? "" : "text-muted-foreground"
              } ${policy.ref === fresh ? "bg-ledger/5" : ""}`}
            >
              <TableCell className="font-mono font-medium">
                {policy.id}
              </TableCell>

              <TableCell className="font-mono">v{policy.version}</TableCell>

              <TableCell className="font-display text-[15px] font-[500]">
                {policy.name}
              </TableCell>

              <TableCell>
                <Badge variant={policy.active ? "ledger" : "outline"}>
                  {policy.active ? "active" : "superseded"}
                </Badge>
              </TableCell>

              {/* The ceiling is inherited, not chosen: a rule may never clear
                  more than the person who approved it could have cleared by
                  hand. It sits next to their name because it is part of who
                  signed this. */}
              <TableCell>
                <span className="flex items-center gap-1.5">
                  <Stamp
                    size={13}
                    weight="fill"
                    className="text-ledger shrink-0"
                    aria-hidden
                  />
                  {/* `approved_by` is the engine's own label — "Chris,
                      Controller" — so the seat is already in it. */}
                  {policy.approved_by}
                </span>
                <span className="text-faint block font-mono text-[11px]">
                  limit {limitLabel(policy.authority_ceiling)} ·{" "}
                  {day(policy.approved_at)}
                </span>
              </TableCell>

              <TableCell className="font-mono text-[12px]">
                {policy.learned_from}
                <span className="text-faint">
                  {" "}
                  · {policy.learned_from_invoice}
                </span>
              </TableCell>

              <TableCell
                className={`text-right font-mono tabular-nums ${
                  cited_by.length ? "text-ledger" : "text-faint"
                }`}
              >
                {cited_by.length}
              </TableCell>

              <TableCell className="text-right font-mono tabular-nums">
                {cleared === null ? (
                  <span className="text-faint">—</span>
                ) : (
                  money(cleared.amount, cleared.currency)
                )}
              </TableCell>

              <TableCell>
                {expanded ? (
                  <CaretDown
                    size={12}
                    weight="bold"
                    className="text-faint"
                    aria-hidden
                  />
                ) : (
                  <CaretRight
                    size={12}
                    weight="bold"
                    className="text-faint"
                    aria-hidden
                  />
                )}
                <span className="sr-only">
                  {expanded ? "Hide the rule" : "Show the rule"}
                </span>
              </TableCell>
            </TableRow>,

            expanded ? (
              <TableRow key={`${policy.ref}-detail`} className="hover:bg-transparent">
                <TableCell colSpan={9} className="pt-0 whitespace-normal">
                  <div className="animate-land bg-mist grid gap-5 rounded-sm px-3 py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
                    <dl className="flex flex-col gap-3">
                      <div>
                        <dt className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
                          When
                        </dt>
                        <dd>
                          <ul className="mt-1 flex flex-col gap-0.5">
                            {conditionLines(row).map((line) => (
                              <li
                                key={line}
                                className="text-muted-foreground text-[12px] leading-relaxed"
                              >
                                {line}
                              </li>
                            ))}
                          </ul>
                        </dd>
                      </div>
                      <div>
                        <dt className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
                          Then
                        </dt>
                        <dd className="mt-1 text-[13px] font-medium">
                          {actionLabel(policy.action)}
                        </dd>
                      </div>
                    </dl>

                    <div className="flex flex-col gap-1.5">
                      <p className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
                        Why
                      </p>
                      <p className="text-muted-foreground text-[12px] leading-relaxed">
                        {policy.rationale}
                        <span className="font-mono">
                          {" "}
                          (
                          {policy.drafted_by === "code"
                            ? "drafted by code"
                            : `drafted by ${policy.drafted_by}, clamped by code`}
                          )
                        </span>
                      </p>
                      <p className="font-mono text-[11px]">
                        <span className="text-faint">cited by </span>
                        <span
                          className={cited_by.length ? "text-ledger" : "text-faint"}
                        >
                          {cited_by.length ? cited_by.join(", ") : "nothing yet"}
                        </span>
                        {policy.supersedes_version !== null ? (
                          <span className="text-faint">
                            {" "}
                            · replaces v{policy.supersedes_version}
                          </span>
                        ) : null}
                      </p>
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            ) : null,
          ];
        })}
      </TableBody>
    </Table>
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
