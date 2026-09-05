import {
  Browser,
  Database,
  EnvelopeSimple,
  type Icon,
} from "@phosphor-icons/react";

import type { Source } from "@/lib/api-types";
import { sourceLabel } from "@/lib/format";

/** The three places Tieout is allowed to look, each with its own mark. */
const MARK: Record<Source, Icon> = {
  erp: Database,
  inbox: EnvelopeSimple,
  portal: Browser,
};

/** A fact without a source is not evidence, so the source is never far from it. */
export function SourceChip({
  source,
  size = 12,
}: {
  source: Source;
  size?: number;
}) {
  const Mark = MARK[source];
  return (
    <span className="surface text-muted inline-flex items-center gap-1.5 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium">
      <Mark size={size} weight="bold" aria-hidden />
      {sourceLabel(source)}
    </span>
  );
}
