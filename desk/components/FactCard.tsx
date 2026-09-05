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
    <article className="surface animate-land rounded-md bg-white p-3.5">
      <header className="flex items-center gap-2">
        <SourceChip source={fact.source} />
        <span className="text-muted text-[12px] font-medium">
          {factKindLabel(fact.kind)}
        </span>
        <span className="text-faint ml-auto font-mono text-[11px]">
          {clock(fact.observed_at)}
        </span>
      </header>

      <p className="mt-2 text-[13px] leading-relaxed">{fact.statement}</p>

      <footer className="mt-2.5 flex flex-wrap items-center gap-x-2 gap-y-1">
        <a
          href={fact.locator}
          target="_blank"
          rel="noreferrer"
          title={fact.locator}
          className="text-faint hover:text-ledger max-w-full truncate font-mono text-[11px] underline decoration-black/15 underline-offset-2"
        >
          {fact.locator}
        </a>
        <span className="text-faint text-[11px]">·</span>
        <span
          className={`font-mono text-[11px] ${
            fact.extracted_by === "code" ? "text-faint" : "text-ledger"
          }`}
        >
          {readerLabel(fact.extracted_by)}
        </span>
      </footer>

      {shot ? (
        <button
          type="button"
          onClick={() => onShowScreenshot?.(fact)}
          title="Show this one in the browser panel"
          className="well mt-3 block w-full overflow-hidden rounded-sm bg-mist"
        >
          <Screenshot
            path={shot}
            alt={`What the browser saw at ${fact.locator}`}
            className="h-[92px] w-full object-cover object-top"
          />
        </button>
      ) : null}
    </article>
  );
}
