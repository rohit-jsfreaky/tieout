import { Camera } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Fact } from "@/lib/api-types";
import { clock, factKindLabel, readerLabel } from "@/lib/format";

import { Screenshot } from "./Screenshot";
import { SourceChip } from "./SourceChip";

/**
 * One line of the audit trail: what was seen, where it came from, when it was
 * read, and whether code or the model read it. A portal fact carries the
 * screenshot the browser took at that moment.
 */
export function FactCard({
  fact,
  onShowScreenshot,
}: {
  fact: Fact;
  onShowScreenshot?: (fact: Fact) => void;
}) {
  const shot = fact.screenshot;
  return (
    <Card size="sm" className="animate-land">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-[13px] font-normal">
          <SourceChip source={fact.source} />
          <span className="text-muted-foreground font-medium">
            {factKindLabel(fact.kind)}
          </span>
        </CardTitle>
        <CardAction>
          <span className="text-faint font-mono text-[11px]">
            {clock(fact.observed_at)}
          </span>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-2.5">
        <p className="text-[13px] leading-relaxed">{fact.statement}</p>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <a
            href={fact.locator}
            target="_blank"
            rel="noreferrer"
            title={fact.locator}
            className="text-faint hover:text-ledger max-w-full truncate font-mono text-[11px] underline decoration-black/15 underline-offset-2"
          >
            {fact.locator}
          </a>
          {fact.extracted_by === "code" ? (
            <span className="text-faint font-mono text-[11px]">
              · {readerLabel(fact.extracted_by)}
            </span>
          ) : (
            <Badge variant="ledger" className="font-mono">
              {readerLabel(fact.extracted_by)}
            </Badge>
          )}
        </div>

        {shot ? (
          <button
            type="button"
            onClick={() => onShowScreenshot?.(fact)}
            title="Show this one in the browser panel"
            className="well group/shot relative block w-full overflow-hidden rounded-sm bg-mist"
          >
            <Screenshot
              path={shot}
              alt={`What the browser saw at ${fact.locator}`}
              className="h-[92px] w-full object-cover object-top"
            />
            <span className="text-faint absolute right-1.5 bottom-1.5 inline-flex items-center gap-1 rounded-full bg-white/90 px-1.5 py-0.5 font-mono text-[10px]">
              <Camera size={10} weight="bold" aria-hidden />
              screenshot
            </span>
          </button>
        ) : null}
      </CardContent>
    </Card>
  );
}
