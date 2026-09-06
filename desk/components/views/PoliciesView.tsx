"use client";

import { Scales } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { money } from "@/lib/format";
import { deskMoney } from "@/lib/totals";
import type { Desk } from "@/lib/useDesk";

import { AuthorityMatrix } from "../AuthorityMatrix";
import { Figure } from "../Figure";
import { PolicyLoopCard } from "../PolicyLoopCard";
import { PolicyTable } from "../PolicyTable";

/**
 * The policy book.
 *
 * Three things, in the order a controller would ask for them: what the rules
 * have done, the rules themselves, and the authority they were signed under.
 * Every rule here was born from exactly one human decision and carries that
 * person's name, their seat and the ceiling their seat imposes — which is why
 * this page can be handed to an auditor rather than explained to one.
 */
export function PoliciesView({ desk }: { desk: Desk }) {
  const total = deskMoney(desk.queue);
  const count = (value: number | undefined) =>
    value === undefined ? undefined : String(value);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-2 xl:grid-cols-4">
        <Figure
          label="Rules in force"
          value={count(desk.metrics?.policies_active)}
          hint="each one learned from a single approval"
          loading={desk.loading}
        />
        <Figure
          label="Times cited"
          value={count(desk.metrics?.policy_citations)}
          hint="decisions that named a rule instead of a person"
          loading={desk.loading}
        />
        <Figure
          label="Human touches avoided"
          value={count(desk.metrics?.touches_avoided_by_policy)}
          hint="exceptions nobody had to look at"
          ledger
          loading={desk.loading}
        />
        <Figure
          label="Cleared for payment"
          value={
            desk.loading ? undefined : money(total.autoApproved, total.currency)
          }
          hint="approved by a rule, on the authority of the person who taught it"
          lead
          loading={desk.loading}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Learned rules</CardTitle>
          <CardDescription>
            One line per rule and per version. Open a line for the condition code
            evaluates and the reason it was written.
          </CardDescription>
          <CardAction>
            <Badge variant="secondary" className="font-mono">
              {desk.loading ? "—" : desk.policies.length}
            </Badge>
          </CardAction>
        </CardHeader>

        <CardContent className="px-0">
          {desk.policies.length === 0 ? (
            <Empty>
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <Scales />
                </EmptyMedia>
                <EmptyTitle>No rules yet</EmptyTitle>
                <EmptyDescription>
                  The first one is born the moment a human approves a decision,
                  and it carries their name. Work an exception and approve it.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            <PolicyTable
              rows={desk.policies}
              queue={desk.queue}
              fresh={desk.learned}
            />
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Delegation of authority</CardTitle>
            <CardDescription>
              {desk.authorityNote ||
                "Read from GET /authority — the desk never states a limit the engine did not publish."}
            </CardDescription>
          </CardHeader>

          <CardContent className="px-0">
            <AuthorityMatrix
              authority={desk.authority}
              policies={desk.policies}
              seat={desk.approver.role}
            />
          </CardContent>
        </Card>

        <PolicyLoopCard />
      </div>
    </div>
  );
}
