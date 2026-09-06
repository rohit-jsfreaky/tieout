import { CircleNotch } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import type { ExceptionStatus } from "@/lib/api-types";
import { statusLabel } from "@/lib/format";

type Variant = React.ComponentProps<typeof Badge>["variant"];

/**
 * Where an exception stands, in one word.
 *
 * The accent is spent on `auto_cleared`, because that is the state the whole
 * project exists to produce; "awaiting a person" and "above their limit" are
 * filled ink, because they are the states that are asking for something.
 */
const TONE: Record<ExceptionStatus, Variant> = {
  open: "outline",
  proposed: "default",
  refused: "outline",
  auto_cleared: "ledger",
  resolved: "secondary",
  escalated: "default",
};

export function StatusBadge({
  status,
  running = false,
}: {
  status: ExceptionStatus;
  running?: boolean;
}) {
  if (running) {
    return (
      <Badge variant="ledger">
        <CircleNotch className="animate-spin" aria-hidden />
        working
      </Badge>
    );
  }
  return <Badge variant={TONE[status]}>{statusLabel(status)}</Badge>;
}
