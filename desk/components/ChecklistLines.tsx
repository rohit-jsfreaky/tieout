"use client";

import { Check as Tick, X } from "@phosphor-icons/react";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Check } from "@/lib/api-types";

/**
 * The written checklist behind a confidence, one line at a time.
 *
 * The right-hand column is the weight each check carries, and it is labelled —
 * a bare 0.15 sitting next to a sentence is a number nobody on the screen can
 * name. `engine/decide.py` gives every exception class this checklist, and the
 * weights that passed ARE the confidence above it.
 */
export function ChecklistLines({ checks }: { checks: Check[] }) {
  if (checks.length === 0) return null;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-faint flex items-baseline justify-between font-mono text-[10px] tracking-[0.1em] uppercase">
        <span>check</span>
        <Tooltip>
          <TooltipTrigger
            render={<span />}
            tabIndex={0}
            className="cursor-help underline decoration-dotted underline-offset-2"
          >
            weight
          </TooltipTrigger>
          <TooltipContent>
            What each check is worth. The weights that passed add up to the
            confidence.
          </TooltipContent>
        </Tooltip>
      </div>

      <ul className="flex flex-col gap-1.5">
        {checks.map((check) => (
          <li key={check.name} className="flex items-start gap-2 text-[12px]">
            {check.passed ? (
              <Tick
                size={13}
                weight="bold"
                className="text-ledger mt-[3px] shrink-0"
                aria-hidden
              />
            ) : (
              <X
                size={13}
                weight="bold"
                className="text-faint mt-[3px] shrink-0"
                aria-hidden
              />
            )}
            <span className={check.passed ? "text-muted-foreground" : "text-faint"}>
              {check.name}
              <span className="text-faint"> — {check.detail}</span>
            </span>
            <span className="text-faint ml-auto shrink-0 font-mono text-[11px]">
              {check.weight.toFixed(2)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
