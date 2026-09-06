"use client";

import { useState } from "react";

import { Camera, CaretRight } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import type { Fact } from "@/lib/api-types";
import { clock, factKindLabel, readerLabel } from "@/lib/format";

import { Screenshot } from "./Screenshot";

/**
 * One fact, one line.
 *
 * Seven facts used to be seven cards, which read as a wall rather than as a
 * trail. A fact is a sentence with a source and a time, so at rest it gets
 * exactly that much room: what it is, what it says, when it was read. The proof
 * — the link, the full text, the screenshot, who read it — is one click away,
 * because a reader checks a fact after the sentence has made them want to.
 */
export function FactRow({
  fact,
  onShowScreenshot,
}: {
  fact: Fact;
  onShowScreenshot?: (fact: Fact) => void;
}) {
  const [open, setOpen] = useState(false);
  const shot = fact.screenshot;

  return (
    <li className="animate-land">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((was) => !was)}
        className="hover:bg-mist flex w-full items-baseline gap-2 rounded-xs px-2 py-1.5 text-left transition-colors"
      >
        <CaretRight
          size={11}
          weight="bold"
          aria-hidden
          className={`text-faint mt-[1px] shrink-0 transition-transform ${
            open ? "rotate-90" : ""
          }`}
        />
        <span className="shrink-0 text-[12.5px] font-medium">
          {factKindLabel(fact.kind)}
        </span>
        <span className="text-muted-foreground min-w-0 flex-1 truncate text-[12.5px]">
          {fact.statement}
        </span>
        {shot ? (
          <Camera
            size={11}
            weight="bold"
            aria-label="has a screenshot"
            className="text-faint shrink-0"
          />
        ) : null}
        <span className="text-faint shrink-0 font-mono text-[11px]">
          {clock(fact.observed_at)}
        </span>
      </button>

      {open ? (
        <div className="flex flex-col gap-2.5 px-2 pt-1 pb-3 pl-[25px]">
          <p className="text-[13px] leading-relaxed">{fact.statement}</p>

          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <a
              href={fact.locator}
              target="_blank"
              rel="noreferrer"
              title={fact.locator}
              className="text-faint hover:text-ledger max-w-full truncate font-mono text-[11px] underline decoration-black/15 underline-offset-2"
            >
              {fact.locator}
            </a>
            {fact.extracted_by === "code" ? (
              <span className="text-faint font-mono text-[11px]">
                · {readerLabel(fact.extracted_by)}
              </span>
            ) : (
              <Badge variant="ledger" className="font-mono">
                {readerLabel(fact.extracted_by)}
              </Badge>
            )}
          </div>

          {shot ? (
            <button
              type="button"
              onClick={() => onShowScreenshot?.(fact)}
              title="Show this one in the browser panel"
              className="well bg-mist relative block w-full overflow-hidden rounded-sm"
            >
              <Screenshot
                path={shot}
                alt={`What the browser saw at ${fact.locator}`}
                className="h-[92px] w-full object-cover object-top"
              />
              <span className="text-faint absolute right-1.5 bottom-1.5 inline-flex items-center gap-1 rounded-full bg-white/90 px-1.5 py-0.5 font-mono text-[10px]">
                <Camera size={10} weight="bold" aria-hidden />
                show in the browser
              </span>
            </button>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
