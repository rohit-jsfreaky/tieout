"use client";

import { useState } from "react";

import { CaretRight } from "@phosphor-icons/react";

/**
 * The reasoning, on a toggle.
 *
 * It is the audit trail, so it is never truncated and never paraphrased — but a
 * paragraph of grey prose under every decision is a wall, and the reader of an
 * auto-cleared exception did not ask for one. So it opens by default on a
 * decision somebody still has to make, and waits to be asked on one that has
 * already cleared itself.
 */
export function WhyThisDecision({
  rationale,
  writtenBy,
  defaultOpen,
}: {
  rationale: string;
  /** `"code"`, `"human"`, or the id of the model that wrote it. */
  writtenBy?: string;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((was) => !was)}
        className="text-muted-foreground hover:text-foreground -ml-1 flex w-fit items-center gap-1.5 rounded-xs px-1 py-0.5 text-[12px] font-medium transition-colors"
      >
        <CaretRight
          size={11}
          weight="bold"
          aria-hidden
          className={`transition-transform ${open ? "rotate-90" : ""}`}
        />
        Why this decision
      </button>

      {open ? (
        <p className="text-muted-foreground text-[13px] leading-relaxed">
          {rationale}
          {writtenBy ? (
            <span className="text-faint font-mono"> ({penLabel(writtenBy)})</span>
          ) : null}
        </p>
      ) : null}
    </div>
  );
}

function penLabel(writtenBy: string): string {
  if (writtenBy === "code") return "written by code";
  if (writtenBy === "human") return "written by hand";
  return `written by ${writtenBy}`;
}
