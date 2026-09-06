"use client";

import { useEffect, useRef } from "react";

import { Play } from "@phosphor-icons/react";

import type {
  DecidableAction,
  EngineEvent,
  ExceptionDetail,
  Fact,
  LookupStep,
} from "@/lib/api-types";
import { exceptionKindLabel, money, sourceLabel } from "@/lib/format";
import type { Approver } from "@/lib/useDesk";

import { DecideBar } from "./DecideBar";
import { DecisionCard } from "./DecisionCard";
import { EmptyNote } from "./EmptyNote";
import { FactCard } from "./FactCard";
import { LiveTrail } from "./LiveTrail";
import { Panel } from "./Panel";
import { RefusalCard } from "./RefusalCard";

/**
 * The evidence pack: every fact as it lands, then the decision — or the refusal.
 *
 * Nothing on this panel is computed here. The facts come off the stream and the
 * pack, the confidence comes off the decision, and the refusal's list of dead
 * ends is the engine's own lookup trail.
 */
export function EvidencePanel({
  detail,
  facts,
  steps,
  live,
  running,
  busy,
  approver,
  approverLimit,
  onWork,
  onDecide,
  onShowScreenshot,
}: {
  detail: ExceptionDetail | null;
  facts: Fact[];
  steps: LookupStep[];
  live: EngineEvent[];
  running: boolean;
  busy: boolean;
  approver: Approver;
  approverLimit: number | null;
  onWork: () => void;
  onDecide: (action: DecidableAction, note: string) => void;
  onShowScreenshot: (fact: Fact) => void;
}) {
  const exception = detail?.exception;
  const decision = detail?.decision ?? lastDecision(live);
  const refused = decision?.action === "refuse";
  const worked = facts.length > 0 || decision !== null;
  // An escalation is NOT settled: nothing was paid, and the pack is still waiting
  // for somebody senior enough, so the decide bar stays open for them.
  const settled =
    decision?.approved_by != null && decision.action !== "escalate";

  // The pack follows itself: the newest fact while evidence is landing, then the
  // verdict, from its first line, the moment there is one to read.
  const foot = useRef<HTMLDivElement>(null);
  const verdict = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (decision) return;
    foot.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [facts.length, decision]);
  useEffect(() => {
    if (!decision) return;
    verdict.current?.scrollIntoView({ block: "start", behavior: "smooth" });
  }, [decision]);

  return (
    <Panel
      title="Evidence pack"
      aside={facts.length ? `${facts.length} facts` : "—"}
      scrolls={false}
    >
      <div className="flex h-full min-h-0 flex-col gap-4">
        {exception ? (
          <header className="shrink-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="font-display text-[19px] leading-tight font-[500]">
                  {exception.invoice_id} · {exception.vendor_name}
                </h2>
                <p className="text-muted mt-1 text-[13px] leading-relaxed">
                  {exception.headline}
                </p>
              </div>
              {!running && !worked ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={onWork}
                  className="bg-ink flex shrink-0 items-center gap-2 rounded-md px-4 py-2 text-[13px] font-medium text-white disabled:opacity-40"
                >
                  <Play size={12} weight="fill" aria-hidden />
                  Work {exception.id}
                </button>
              ) : null}
            </div>

            <dl className="text-muted mt-3 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px]">
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
          </header>
        ) : (
          <EmptyNote>Pick an exception from the queue.</EmptyNote>
        )}

        {/* Only while it is happening. Once the run is over every step of it is
            in the facts below and in the decision's own checklist, and the pack
            is what a person reads. */}
        {running && live.length > 0 ? (
          <div className="shrink-0">
            <LiveTrail events={live} />
          </div>
        ) : null}

        {/* The pack reads as one document: the facts in the order they landed,
            then what Tieout wants to do about them. It follows the newest thing
            on screen, so a run watched from across a room stays legible. */}
        <div className="-mx-1 min-h-0 flex-1 space-y-2 overflow-y-auto px-1">
          {facts.length === 0 && !running && exception ? (
            <EmptyNote>
              Nothing has been gathered yet. Press Work {exception.id} and the ERP,
              the vendor&apos;s mail and the VendorLink portal are read in that
              order — each fact lands here with its source, its link, the time and
              whether code or the model read it.
            </EmptyNote>
          ) : null}

          {facts.map((fact) => (
            <FactCard
              key={fact.id}
              fact={fact}
              onShowScreenshot={onShowScreenshot}
            />
          ))}

          {facts.length > 0 && !refused ? (
            <p className="text-faint pt-1 font-mono text-[11px]">
              looked in {steps.length} places across{" "}
              {(detail?.pack?.sources_used ?? []).map(sourceLabel).join(", ") ||
                "—"}
            </p>
          ) : null}

          {decision ? (
            <div ref={verdict} className="scroll-mt-2 pt-2">
              {refused ? (
                <RefusalCard
                  decision={decision}
                  steps={steps}
                  approver={approver}
                  approverLimit={approverLimit}
                />
              ) : (
                <DecisionCard
                  decision={decision}
                  approver={approver}
                  approverLimit={approverLimit}
                />
              )}
            </div>
          ) : null}

          <div ref={foot} />
        </div>

        {decision && !decision.auto && !settled ? (
          <div className="shrink-0 border-t border-black/6 pt-1">
            <DecideBar
              approver={approver}
              busy={busy}
              disabled={running}
              onDecide={onDecide}
            />
          </div>
        ) : null}
      </div>
    </Panel>
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
