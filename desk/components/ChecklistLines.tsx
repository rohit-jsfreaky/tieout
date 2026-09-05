import { Check as Tick, X } from "@phosphor-icons/react";

import type { Check } from "@/lib/api-types";

/** The written checklist behind a confidence, one line at a time. */
export function ChecklistLines({ checks }: { checks: Check[] }) {
  if (checks.length === 0) return null;
  return (
    <ul className="mt-3 space-y-1.5">
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
          <span className={check.passed ? "text-muted" : "text-faint"}>
            {check.name}
            <span className="text-faint"> — {check.detail}</span>
          </span>
          <span className="text-faint ml-auto shrink-0 font-mono text-[11px]">
            {check.weight.toFixed(2)}
          </span>
        </li>
      ))}
    </ul>
  );
}
