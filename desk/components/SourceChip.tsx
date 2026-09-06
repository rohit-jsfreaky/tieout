import {
  Browser,
  Database,
  EnvelopeSimple,
  type Icon,
} from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import type { Source } from "@/lib/api-types";
import { sourceLabel } from "@/lib/format";

/** The three places Tieout is allowed to look, each with its own mark. */
const MARK: Record<Source, Icon> = {
  erp: Database,
  inbox: EnvelopeSimple,
  portal: Browser,
};

/** A fact without a source is not evidence, so the source is never far from it. */
export function SourceChip({ source }: { source: Source }) {
  const Mark = MARK[source];
  return (
    <Badge variant="outline">
      <Mark weight="bold" aria-hidden />
      {sourceLabel(source)}
    </Badge>
  );
}
