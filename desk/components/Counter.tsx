import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * One figure in the strip.
 *
 * `value` is null until a real run supplies it — this screen never invents a
 * number. `winning` marks the one the demo is about: human touches.
 */
export function Counter({
  label,
  value,
  loading,
  winning = false,
}: {
  label: string;
  value: number | undefined;
  loading: boolean;
  winning?: boolean;
}) {
  return (
    <Card size="sm">
      <CardHeader className="gap-1.5">
        <CardDescription className="text-[11px] font-medium tracking-[0.1em] uppercase">
          {label}
        </CardDescription>
        {loading ? (
          <Skeleton className="h-6 w-8" />
        ) : (
          <CardTitle
            className={`font-mono text-[26px] leading-none font-medium ${
              value === undefined
                ? "text-faint"
                : winning
                  ? "text-ledger"
                  : "text-foreground"
            }`}
          >
            {value ?? "—"}
          </CardTitle>
        )}
      </CardHeader>
    </Card>
  );
}
