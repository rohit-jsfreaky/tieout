"use client";

import { useState } from "react";

import type { Fact } from "@/lib/api-types";
import { useDesk } from "@/lib/useDesk";

import { BrowserPanel } from "./BrowserPanel";
import { ControlBar } from "./ControlBar";
import { CounterStrip } from "./CounterStrip";
import { ErrorBanner } from "./ErrorBanner";
import { EvidencePanel } from "./EvidencePanel";
import { Masthead } from "./Masthead";
import { PoliciesPanel } from "./PoliciesPanel";
import { QueuePanel } from "./QueuePanel";

/**
 * The one screen.
 *
 * Queue, evidence pack, live browser and policies, over the counters and the
 * controls. Every value on it came from the API in this session; there is no
 * mock mode and no seeded number anywhere in this folder.
 */
export function Desk() {
  const desk = useDesk();
  const [pinned, setPinned] = useState<Fact | null>(null);

  const running = desk.runningId !== null && desk.runningId === desk.selectedId;
  const busy = desk.pending !== null;

  // The browser panel follows the run: the newest screenshot, unless a fact card
  // was clicked, and only while that fact still belongs to the pack on screen.
  const shots = desk.facts.filter((fact) => fact.screenshot);
  const held = pinned && shots.some((fact) => fact.id === pinned.id) ? pinned : null;
  const shown = held ?? shots[shots.length - 1] ?? null;

  return (
    <div className="flex h-dvh flex-col">
      <header className="hairline shrink-0">
        <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-5 px-6 py-6">
          <Masthead />
          <CounterStrip metrics={desk.metrics} />
        </div>
      </header>

      {desk.error ? (
        <ErrorBanner message={desk.error} onDismiss={desk.dismissError} />
      ) : null}

      <main className="min-h-0 flex-1">
        <div className="mx-auto grid h-full w-full max-w-[1440px] grid-cols-[19rem_minmax(0,1fr)_23rem] divide-x divide-black/6">
          <QueuePanel
            queue={desk.queue}
            selectedId={desk.selectedId}
            runningId={desk.runningId}
            loading={desk.loading}
            onSelect={desk.select}
          />

          <EvidencePanel
            detail={desk.detail}
            facts={desk.facts}
            steps={desk.steps}
            live={desk.live}
            running={running}
            busy={busy}
            approver={desk.approver}
            approverLimit={desk.approverLimit}
            onWork={() => desk.selectedId && desk.work(desk.selectedId)}
            onDecide={desk.decide}
            onShowScreenshot={setPinned}
          />

          <div className="grid min-h-0 min-w-0 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,20rem)_minmax(0,1fr)] divide-y divide-black/6">
            <BrowserPanel
              fact={shown}
              steps={desk.steps.filter((step) => step.source === "portal")}
              running={running}
            />
            <PoliciesPanel policies={desk.policies} learned={desk.learned} />
          </div>
        </div>
      </main>

      <footer className="shrink-0 border-t border-black/6 bg-soft">
        <div className="mx-auto w-full max-w-[1440px] px-6 py-4">
          <ControlBar
            approver={desk.approver}
            setApprover={desk.setApprover}
            authority={desk.authority}
            nextId={desk.nextId}
            pending={desk.pending}
            onWorkNext={() => desk.nextId && desk.work(desk.nextId)}
            onReset={desk.reset}
          />
        </div>
      </footer>
    </div>
  );
}
