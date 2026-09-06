import { Browser, CircleNotch, Lock } from "@phosphor-icons/react";

import type { Fact, LookupStep } from "@/lib/api-types";
import { clock } from "@/lib/format";

import { EmptyNote } from "./EmptyNote";
import { Eyebrow } from "./Eyebrow";
import { Screenshot } from "./Screenshot";

/**
 * What the agent's browser is looking at, without leaving the desk.
 *
 * VendorLink has no API, so `engine/sources/portal.py` drives a real Chromium:
 * it signs in, reads the delivery note off the rendered page and screenshots it
 * as evidence. That PNG arrives on the SSE stream attached to its Fact, and this
 * panel shows the latest one — so the sign-in happens on camera, in the product,
 * rather than in a second window nobody can see.
 *
 * It is the widest thing on the view and the quietest: the page fills the column
 * edge to edge, with a chrome around it and nothing competing for the eye. A
 * screenshot nobody can read is not evidence.
 */
export function BrowserPanel({
  fact,
  steps,
  running,
}: {
  fact: Fact | null;
  steps: LookupStep[];
  running: boolean;
}) {
  const latest = steps.length > 0 ? steps[steps.length - 1] : null;

  return (
    <section className="flex min-h-0 min-w-0 flex-col">
      <header className="hairline flex shrink-0 items-center justify-between gap-3 px-4 py-2.5">
        <Eyebrow>Live browser</Eyebrow>
        <span className="text-faint shrink-0 font-mono text-[11px]">
          {running && !fact ? "opening…" : "VendorLink"}
        </span>
      </header>

      <div className="hairline flex min-w-0 shrink-0 items-center gap-2 bg-soft px-2.5 py-2">
        <span className="flex shrink-0 gap-1" aria-hidden>
          <Dot />
          <Dot />
          <Dot />
        </span>
        <span className="well text-faint flex min-w-0 flex-1 items-center gap-1.5 rounded-full bg-white px-2.5 py-1 font-mono text-[10px]">
          <Lock size={9} weight="bold" aria-hidden />
          <span className="truncate">
            {fact?.locator ?? latest?.locator ?? "about:blank"}
          </span>
        </span>
      </div>

      {/* As tall as the page it is showing, and no taller — a band of empty
          grey under a screenshot reads as something that failed to load. */}
      <div className="bg-mist max-h-[calc(100svh-16rem)] min-h-[15rem] overflow-y-auto">
        {fact ? (
          <Screenshot
            path={fact.screenshot ?? ""}
            alt={`VendorLink at ${fact.locator}`}
            className="block w-full"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
            {running ? (
              <span className="text-faint inline-flex items-center gap-2 text-[13px]">
                <CircleNotch size={13} weight="bold" className="animate-spin" aria-hidden />
                signing in to VendorLink…
              </span>
            ) : (
              <>
                <span className="surface flex size-11 items-center justify-center rounded-full bg-white">
                  <Browser size={18} weight="regular" className="text-faint" aria-hidden />
                </span>
                <EmptyNote>
                  The vendor portal has no API, so Tieout drives a real browser.
                  Every page it reads is screenshotted into the evidence pack and
                  appears here.
                </EmptyNote>
              </>
            )}
          </div>
        )}
      </div>

      {latest ? (
        <p className="text-faint hairline-top shrink-0 truncate px-4 py-2 font-mono text-[11px]">
          {clock(latest.at)} · {latest.action}
        </p>
      ) : null}
    </section>
  );
}

function Dot() {
  return <span className="size-2 rounded-full bg-black/10" />;
}
