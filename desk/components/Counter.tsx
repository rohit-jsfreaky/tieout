/** One figure in the strip. `value` is null until a real run supplies it — this
 *  screen never invents a number. `winning` marks the one the demo is about. */
export function Counter({
  label,
  value,
  winning = false,
}: {
  label: string;
  value: string | null;
  winning?: boolean;
}) {
  return (
    <div className="surface flex-1 rounded-md bg-white px-4 py-3">
      <div className="text-faint text-[11px] font-medium tracking-[0.1em] uppercase">
        {label}
      </div>
      <div
        className={`font-mono text-[26px] leading-none font-medium ${
          winning ? "text-ledger" : "text-ink"
        } ${value === null ? "text-faint" : ""}`}
      >
        {value ?? "—"}
      </div>
    </div>
  );
}
