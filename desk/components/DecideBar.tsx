"use client";

import { useState } from "react";

import type { DecidableAction } from "@/lib/api-types";

/**
 * The one human touch.
 *
 * Approve means "do what Tieout proposed" — the engine resolves it into the real
 * action and records that. Edit is for the times it proposed the wrong thing:
 * pick what should happen instead and say why, in the same breath.
 */
const EDITS: { value: DecidableAction; label: string }[] = [
  { value: "short_pay", label: "Short-pay the difference" },
  { value: "attach_po", label: "Attach the purchase order" },
  { value: "approve", label: "Approve in full" },
  { value: "reject", label: "Reject the invoice" },
];

export function DecideBar({
  approver,
  busy,
  disabled,
  onDecide,
}: {
  approver: string;
  busy: boolean;
  disabled: boolean;
  onDecide: (action: DecidableAction, note: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [action, setAction] = useState<DecidableAction>("short_pay");
  const [note, setNote] = useState("");

  const send = (chosen: DecidableAction) => {
    onDecide(chosen, note.trim());
    setEditing(false);
    setNote("");
  };

  const stop = busy || disabled;

  return (
    <div className="mt-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={stop}
          onClick={() => send("approve")}
          className="bg-ledger rounded-md px-4 py-2 text-[13px] font-medium text-white disabled:opacity-40"
        >
          {busy ? "Recording…" : "Approve"}
        </button>
        <button
          type="button"
          disabled={stop}
          onClick={() => send("reject")}
          className="surface rounded-md bg-white px-4 py-2 text-[13px] font-medium disabled:opacity-40"
        >
          Reject
        </button>
        <button
          type="button"
          disabled={stop}
          onClick={() => setEditing((open) => !open)}
          className="surface rounded-md bg-white px-4 py-2 text-[13px] font-medium disabled:opacity-40"
          aria-expanded={editing}
        >
          Edit
        </button>
        <span className="text-faint ml-auto text-[12px]">
          as {approver.trim() || "— nobody —"}
        </span>
      </div>

      {editing ? (
        <div className="surface mt-3 rounded-md bg-white p-3">
          <label className="text-faint block text-[11px] font-medium tracking-[0.1em] uppercase">
            Do this instead
          </label>
          <select
            value={action}
            onChange={(event) =>
              setAction(event.target.value as DecidableAction)
            }
            className="well mt-2 w-full rounded-sm bg-soft px-3 py-2 text-[13px] outline-none"
          >
            {EDITS.map((edit) => (
              <option key={edit.value} value={edit.value}>
                {edit.label}
              </option>
            ))}
          </select>

          <label className="text-faint mt-3 block text-[11px] font-medium tracking-[0.1em] uppercase">
            Why — this goes on the rule
          </label>
          <input
            type="text"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Northwind always ships the balance next week."
            className="well placeholder:text-faint mt-2 w-full rounded-sm bg-soft px-3 py-2 text-[13px] outline-none"
          />

          <button
            type="button"
            disabled={stop}
            onClick={() => send(action)}
            className="bg-ink mt-3 rounded-md px-4 py-2 text-[13px] font-medium text-white disabled:opacity-40"
          >
            Record it
          </button>
        </div>
      ) : null}
    </div>
  );
}
