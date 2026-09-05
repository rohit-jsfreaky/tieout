import { percent } from "@/lib/format";

/**
 * The confidence, drawn as a recessed track.
 *
 * It is not a feeling: `engine/decide.py` gives every class a written checklist
 * and the confidence is the weight that passed, so the checks printed under this
 * bar add up to the number on it.
 */
export function ConfidenceBar({
  value,
  tone = "ledger",
}: {
  value: number;
  tone?: "ledger" | "quiet";
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="well h-1.5 flex-1 overflow-hidden rounded-xs bg-mist">
        <div
          className={`h-full rounded-xs transition-[width] duration-700 ease-out ${
            tone === "ledger" ? "bg-ledger" : "bg-faint"
          }`}
          style={{ width: `${Math.round(Math.min(Math.max(value, 0), 1) * 100)}%` }}
        />
      </div>
      <span
        className={`font-mono text-[13px] font-medium ${
          tone === "ledger" ? "text-ledger" : "text-muted"
        }`}
      >
        {percent(value)}
      </span>
    </div>
  );
}
