/** The whole demo is driven from this row: who is approving, work the next
 *  exception, put the world back to the seed. Wired in 4b/4c. */
export function ControlBar() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-muted flex items-center gap-2 text-[13px]">
        <span className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
          Approver
        </span>
        <input
          type="text"
          name="approver"
          placeholder="Chris, Controller"
          disabled
          className="well placeholder:text-faint w-56 rounded-md bg-soft px-3 py-2 text-[13px] outline-none"
        />
      </label>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          disabled
          className="surface rounded-md bg-white px-4 py-2 text-[13px] font-medium disabled:opacity-60"
        >
          Reset
        </button>
        <button
          type="button"
          disabled
          className="bg-ink rounded-md px-5 py-2 text-[13px] font-medium text-white disabled:opacity-60"
        >
          Work next
        </button>
      </div>
    </div>
  );
}
