"use client";

import { ArrowCounterClockwise, Play } from "@phosphor-icons/react";

import type { Pending } from "@/lib/useDesk";

/**
 * The whole demo is driven from this row: who is approving, work the next
 * exception nobody has touched, and put the world back to the seed.
 *
 * The approver's name is not decoration — it is stamped onto every rule the
 * approval creates, and every later auto-clear cites it.
 */
export function ControlBar({
  approver,
  setApprover,
  nextId,
  pending,
  onWorkNext,
  onReset,
}: {
  approver: string;
  setApprover: (name: string) => void;
  nextId: string | null;
  pending: Pending;
  onWorkNext: () => void;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-muted flex items-center gap-2 text-[13px]">
        <span className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          Approver
        </span>
        <input
          type="text"
          name="approver"
          value={approver}
          onChange={(event) => setApprover(event.target.value)}
          placeholder="Chris, Controller"
          className="well placeholder:text-faint w-56 rounded-md bg-soft px-3 py-2 text-[13px] outline-none"
        />
      </label>

      <span className="text-faint text-[12px]">
        goes on every rule this approval creates
      </span>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={onReset}
          disabled={pending !== null}
          className="surface flex items-center gap-2 rounded-md bg-white px-4 py-2 text-[13px] font-medium disabled:opacity-40"
        >
          <ArrowCounterClockwise size={12} weight="bold" aria-hidden />
          {pending === "reset" ? "Resetting…" : "Reset"}
        </button>
        <button
          type="button"
          onClick={onWorkNext}
          disabled={pending !== null || nextId === null}
          className="bg-ink flex items-center gap-2 rounded-md px-5 py-2 text-[13px] font-medium text-white disabled:opacity-40"
        >
          <Play size={12} weight="fill" aria-hidden />
          {pending === "work"
            ? "Working…"
            : nextId
              ? `Work next — ${nextId}`
              : "Nothing left to work"}
        </button>
      </div>
    </div>
  );
}
