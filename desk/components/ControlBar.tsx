"use client";

import { ArrowCounterClockwise, Play } from "@phosphor-icons/react";

import type { AuthorityRow, Role } from "@/lib/api-types";
import { limitLabel } from "@/lib/format";
import type { Approver, Pending } from "@/lib/useDesk";

/**
 * The whole demo is driven from this row: who is approving and what they are
 * allowed to approve, work the next exception nobody has touched, and put the
 * world back to the seed.
 *
 * The approver is not decoration and it is not just a name. The seat carries a
 * limit from the company's delegation-of-authority matrix; that limit is stamped
 * onto every rule the approval creates, and no later auto-clear can exceed it.
 */
export function ControlBar({
  approver,
  setApprover,
  authority,
  nextId,
  pending,
  onWorkNext,
  onReset,
}: {
  approver: Approver;
  setApprover: (approver: Approver) => void;
  authority: AuthorityRow[];
  nextId: string | null;
  pending: Pending;
  onWorkNext: () => void;
  onReset: () => void;
}) {
  const seat = authority.find((row) => row.role === approver.role);

  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-muted flex items-center gap-2 text-[13px]">
        <span className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          Approver
        </span>
        <input
          type="text"
          name="approver"
          value={approver.name}
          onChange={(event) =>
            setApprover({ ...approver, name: event.target.value })
          }
          placeholder="Chris"
          className="well placeholder:text-faint w-40 rounded-md bg-soft px-3 py-2 text-[13px] outline-none"
        />
      </label>

      <label className="text-muted flex items-center gap-2 text-[13px]">
        <span className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          Role
        </span>
        <select
          name="role"
          value={approver.role}
          onChange={(event) =>
            setApprover({ ...approver, role: event.target.value as Role })
          }
          className="well rounded-md bg-soft px-3 py-2 text-[13px] outline-none"
        >
          {authority.length === 0 ? (
            <option value={approver.role}>{approver.role}</option>
          ) : (
            authority.map((row) => (
              <option key={row.role} value={row.role}>
                {row.role}
              </option>
            ))
          )}
        </select>
      </label>

      <span className="text-faint text-[12px]">
        {/* Before the matrix has landed the limit is unknown, which is not the
            same thing as unlimited — so say nothing rather than say "no limit". */}
        may approve {seat ? limitLabel(seat.limit) : "—"} · that limit goes on
        every rule this approval creates
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
