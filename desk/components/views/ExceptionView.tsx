"use client";

import { useState } from "react";

import { FileMagnifyingGlass, Play } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
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

import { AuthorityNote, aboveAuthority } from "../AuthorityNote";
import { BrowserPanel } from "../BrowserPanel";
import { DecideBar } from "../DecideBar";
import { DecisionCard } from "../DecisionCard";
import { EvidenceList } from "../EvidenceList";
import { Figure, FigureRow } from "../FigureRow";
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
 * It reads top to bottom in the order it matters: which invoice, what Tieout
 * decided, what it found — and down the right, filling its column, what its
 * browser was looking at while it found it. The decision is the biggest thing
 * on the view; the evidence under it is a trail of one-line facts, each opened
 * when somebody wants to check that one.
 */
export function ExceptionView({ desk }: { desk: Desk }) {
  const [pinned, setPinned] = useState<Fact | null>(null);

  const exception = desk.detail?.exception;
  const decision = desk.detail?.decision ?? lastDecision(desk.live);
  const refused = decision?.action === "refuse";
  const escalated = decision?.action === "escalate";
  const running = desk.runningId !== null && desk.runningId === desk.selectedId;
  const busy = desk.pending !== null;
  const worked = desk.facts.length > 0 || decision !== null;
  // An escalation is deliberately not settled: nothing was paid and nothing was
  // learned, so the decide bar stays open — change the seat and the same pack
  // goes through. That is the fifth beat.
  const settled = decision?.approved_by != null && !escalated;
  const blocked = aboveAuthority(decision, desk.approverSeat);

  // The browser panel follows the run: the newest screenshot, unless a fact was
  // clicked, and only while that fact still belongs to the pack on screen.
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
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_30rem]">
      <div className="flex min-w-0 flex-col gap-5">
        {/* Which invoice. Context rather than the point, so it is the small type
            and the one status badge on the view. */}
        <Card size="sm">
          <CardHeader>
            <CardTitle className="font-display text-[16px] leading-tight font-[500]">
              {exception.invoice_id} · {exception.vendor_name}
            </CardTitle>
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

          <CardContent className="flex flex-col gap-1.5">
            <p className="text-muted-foreground text-[13px] leading-snug">
              {exception.headline}
            </p>
            <FigureRow>
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
            </FigureRow>
          </CardContent>
        </Card>

        {/* Only while it is happening. Once the run is over every step of it is
            in the facts below and in the checklist on the decision, and the pack
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

        {/* E5 reads as both at once, which is the point: refused for want of
            evidence, AND above the seat at this desk. Two independent reasons
            this cannot end here. */}
        {decision && !decision.auto ? (
          <AuthorityNote
            decision={decision}
            approver={desk.approver}
            seat={desk.approverSeat}
          />
        ) : null}

        {decision && !decision.auto && !settled ? (
          <DecideBar
            approver={desk.approver}
            setApprover={desk.setApprover}
            authority={desk.authority}
            busy={busy}
            disabled={running}
            blocked={blocked}
            onDecide={desk.decide}
          />
        ) : null}

        <Card size="sm">
          <CardHeader>
            <CardTitle className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
              Evidence
            </CardTitle>
            <CardAction>
              <span className="text-faint font-mono text-[11px]">
                {desk.facts.length > 0
                  ? `${desk.facts.length} facts · ${desk.steps.length} places · ${
                      (desk.detail?.pack?.sources_used ?? [])
                        .map(sourceLabel)
                        .join(", ") || "—"
                    }`
                  : "—"}
              </span>
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

            {desk.facts.length > 0 ? (
              <EvidenceList facts={desk.facts} onShowScreenshot={setPinned} />
            ) : null}

            {desk.facts.length === 0 && running ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* The best thing on the screen, so it gets the whole column and stays in
          view while the evidence scrolls past it. */}
      <div className="min-w-0 xl:sticky xl:top-0 xl:self-start">
        <Card className="overflow-hidden py-0">
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

/** During a run the decision arrives on the stream before the pack is refetched. */
function lastDecision(live: EngineEvent[]) {
  for (let index = live.length - 1; index >= 0; index -= 1) {
    const decision = live[index].decision;
    if (decision) return decision;
  }
  return null;
}
