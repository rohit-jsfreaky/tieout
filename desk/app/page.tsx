import { ControlBar } from "@/components/ControlBar";
import { CounterStrip } from "@/components/CounterStrip";
import { EvidencePanel } from "@/components/EvidencePanel";
import { Masthead } from "@/components/Masthead";
import { PoliciesPanel } from "@/components/PoliciesPanel";
import { QueuePanel } from "@/components/QueuePanel";

/** The one screen. Four zones: the counters on top, then queue, evidence pack
 *  and policies side by side, with the controls along the bottom. */
export default function Desk() {
  return (
    <div className="flex h-dvh flex-col">
      <header className="hairline shrink-0">
        <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-5 px-6 py-6">
          <Masthead />
          <CounterStrip />
        </div>
      </header>

      <main className="min-h-0 flex-1">
        <div className="mx-auto grid h-full w-full max-w-[1280px] grid-cols-[20rem_minmax(0,1fr)_21rem] divide-x divide-black/6">
          <QueuePanel />
          <EvidencePanel />
          <PoliciesPanel />
        </div>
      </main>

      <footer className="shrink-0 border-t border-black/6 bg-soft">
        <div className="mx-auto w-full max-w-[1280px] px-6 py-4">
          <ControlBar />
        </div>
      </footer>
    </div>
  );
}
