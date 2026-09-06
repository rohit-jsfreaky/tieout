import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * One figure on a strip — a sum of money, or a count.
 *
 * `value` is already formatted, and it is `undefined` until a real run supplies
 * it: this screen prints "—" rather than inventing a zero. `lead` is for the
 * money row, which is set larger than the counts because this is a finance
 * product and the money is the headline. `ledger` marks the one figure the demo
 * is about — the accent is never decoration here.
 */
export function Figure({
  label,
  value,
  hint,
  lead = false,
  ledger = false,
  loading = false,
}: {
  label: string;
  value: string | undefined;
  hint?: string;
  lead?: boolean;
  ledger?: boolean;
  loading?: boolean;
}) {
  return (
    <Card size="sm">
      <CardHeader className="gap-1.5">
        <CardDescription className="text-[11px] font-medium tracking-[0.1em] uppercase">
          {label}
        </CardDescription>

        {loading ? (
          <Skeleton className={lead ? "h-6 w-28" : "h-5 w-10"} />
        ) : (
          <CardTitle
            className={`font-mono leading-none font-medium tabular-nums ${
              lead ? "text-[24px]" : "text-[20px]"
            } ${
              value === undefined
                ? "text-faint"
                : ledger
                  ? "text-ledger"
                  : "text-foreground"
            }`}
          >
            {value ?? "—"}
          </CardTitle>
        )}

        {hint ? (
          <p className="text-faint text-[11px] leading-snug">{hint}</p>
        ) : null}
      </CardHeader>
    </Card>
  );
}
