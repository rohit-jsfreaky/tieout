"use client";

import { useEffect, useRef } from "react";

import type { EngineEvent } from "@/lib/api-types";
import { clock } from "@/lib/format";

/**
 * The engine talking, live.
 *
 * Every line is one `engine.events.Event` forwarded over SSE without being
 * reshaped, so what a judge reads here is what the engine actually said —
 * including the sign-in to VendorLink, as it happens.
 */
export function LiveTrail({ events }: { events: EngineEvent[] }) {
  const foot = useRef<HTMLDivElement>(null);

  useEffect(() => {
    foot.current?.scrollIntoView({ block: "nearest" });
  }, [events.length]);

  if (events.length === 0) return null;

  return (
    <div className="well max-h-28 overflow-y-auto rounded-md bg-soft px-3 py-2">
      <ul className="space-y-1">
        {events.map((event, index) => (
          <li
            key={`${event.at}-${index}`}
            className="flex items-start gap-2 text-[12px] leading-snug"
          >
            <span className="text-faint shrink-0 font-mono text-[11px]">
              {clock(event.at)}
            </span>
            <span
              className={
                event.kind === "auto_cleared" || event.kind === "policy_learned"
                  ? "text-ledger font-medium"
                  : "text-muted"
              }
            >
              {event.message}
            </span>
          </li>
        ))}
      </ul>
      <div ref={foot} />
    </div>
  );
}
