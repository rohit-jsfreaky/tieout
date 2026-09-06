"use client";

import { useState } from "react";

import { FileMagnifyingGlass, Play } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import type { EngineEvent, Fact } from "@/lib/api-types";
import { exceptionKindLabel, money, sourceLabel } from "@/lib/format";
import type { Desk } from "@/lib/useDesk";

import { BrowserPanel } from "../BrowserPanel";
import { DecideBar } from "../DecideBar";
import { DecisionCard } from "../DecisionCard";
import { FactCard } from "../FactCard";
import { LiveTrail } from "../LiveTrail";
import { RefusalCard } from "../RefusalCard";
import { StatusBadge } from "../StatusBadge";

/**
 * The evidence pack: every fact as it lands, then the decision — or the refusal.
 *
 * Nothing on this view is computed here. The facts come off the stream and the
 * pack, the confidence comes off the decision, and the refusal's list of dead
 * ends is the engine's own lookup trail.
 *
 * The verdict sits above the evidence on purpose: the person reading it has to
 * decide, and then check. The evidence is right underneath, in the order it
 * landed, and it is never truncated.
 */
export function ExceptionView({ desk }: { desk: Desk }) {
  const [pinned, setPinned] = useState<Fact | null>(null);

  const exception = desk.detail?.exception;
  const decision = desk.detail?.decision ?? lastDecision(desk.live);
  const refused = decision?.action === "refuse";
  const running = desk.runningId !== null && desk.runningId === desk.selectedId;
  const busy = desk.pending !== null;
  const worked = desk.facts.length > 0 || decision !== null;
  const settled = decision?.approved_by != null;

  // The browser panel follows the run: the newest screenshot, unless a fact card
  // was clicked, and only while that fact still belongs to the pack on screen.
  const shots = desk.facts.filter((fact) => fact.screenshot);
  const held = pinned && shots.some((fact) => fact.id === pinned.id) ? pinned : null;
  const shown = held ?? shots[shots.length - 1] ?? null;

  if (!desk.selectedId) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <FileMagnifyingGlass />
          </EmptyMedia>
          <EmptyTitle>No exception open</EmptyTitle>
          <EmptyDescription>
            Pick one from the queue and its evidence pack appears here.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button variant="outline" onClick={() => desk.setView("queue")}>
            Back to the queue
          </Button>
        </EmptyContent>
      </Empty>
    );
  }

  if (!exception) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_25rem]">
      <div className="flex min-w-0 flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="font-display text-[19px] leading-tight font-[500]">
              {exception.invoice_id} · {exception.vendor_name}
            </CardTitle>
            <CardDescription>{exception.headline}</CardDescription>
            <CardAction>
              {!running && !worked ? (
                <Button size="lg" disabled={busy} onClick={() => desk.work(exception.id)}>
                  {busy ? (
                    <Spinner data-icon="inline-start" />
                  ) : (
                    <Play weight="fill" data-icon="inline-start" />
                  )}
                  Work {exception.id}
                </Button>
              ) : (
                <StatusBadge status={exception.status} running={running} />
              )}
            </CardAction>
          </CardHeader>

          <CardContent>
            <dl className="text-muted-foreground flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px]">
              <Figure label="id" value={exception.id} />
              <Figure label="class" value={exceptionKindLabel(exception.kind)} />
              <Figure
                label="billed"
                value={money(exception.amount, exception.currency)}
              />
              <Figure
                label="at stake"
                value={money(exception.exposure, exception.currency)}
              />
              {exception.po_id ? (
                <Figure label="order" value={exception.po_id} />
              ) : null}
            </dl>
          </CardContent>
        </Card>

        {/* Only while it is happening. Once the run is over every step of it is
            in the facts below and in the decision's own checklist, and the pack
            is what a person reads. */}
        {running && desk.live.length > 0 ? (
          <LiveTrail events={desk.live} />
        ) : null}

        {decision ? (
          refused ? (
            <RefusalCard decision={decision} steps={desk.steps} />
          ) : (
            <DecisionCard decision={decision} />
          )
        ) : null}

        {decision && !decision.auto && !settled ? (
          <DecideBar
            approver={desk.approver}
            setApprover={desk.setApprover}
            busy={busy}
            disabled={running}
            onDecide={desk.decide}
          />
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Evidence</CardTitle>
            <CardDescription>
              {desk.facts.length > 0
                ? `Looked in ${desk.steps.length} places across ${
                    (desk.detail?.pack?.sources_used ?? [])
                      .map(sourceLabel)
                      .join(", ") || "—"
                  }.`
                : "Every fact carries its source, its link, the time, and whether code or the model read it."}
            </CardDescription>
            <CardAction>
              <Badge variant="secondary" className="font-mono">
                {desk.facts.length || "—"}
              </Badge>
            </CardAction>
          </CardHeader>

          <CardContent className="flex flex-col gap-2">
            {desk.facts.length === 0 && !running ? (
              <Empty>
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <FileMagnifyingGlass />
                  </EmptyMedia>
                  <EmptyTitle>Nothing gathered yet</EmptyTitle>
                  <EmptyDescription>
                    Press Work {exception.id} and the ERP, the vendor&apos;s mail
                    and the VendorLink portal are read in that order.
                  </EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button disabled={busy} onClick={() => desk.work(exception.id)}>
                    <Play weight="fill" data-icon="inline-start" />
                    Work {exception.id}
                  </Button>
                </EmptyContent>
              </Empty>
            ) : null}

            {desk.facts.map((fact) => (
              <FactCard key={fact.id} fact={fact} onShowScreenshot={setPinned} />
            ))}

            {desk.facts.length === 0 && running ? (
              <>
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="min-w-0 xl:sticky xl:top-0 xl:self-start">
        <Card className="h-[28rem] py-0">
          <BrowserPanel
            fact={shown}
            steps={desk.steps.filter((step) => step.source === "portal")}
            running={running}
          />
        </Card>
      </div>
    </div>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt className="text-faint">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

/** During a run the decision arrives on the stream before the pack is refetched. */
function lastDecision(live: EngineEvent[]) {
  for (let index = live.length - 1; index >= 0; index -= 1) {
    const decision = live[index].decision;
    if (decision) return decision;
  }
  return null;
}
