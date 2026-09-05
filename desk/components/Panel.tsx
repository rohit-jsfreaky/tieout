import { Eyebrow } from "./Eyebrow";

/**
 * One of the zones: a titled column that scrolls on its own, so the counters and
 * the controls never leave the screen.
 *
 * `scrolls={false}` hands the scrolling to the panel's own contents — the
 * evidence pack keeps the proposed decision and the Approve button pinned while
 * the facts scroll behind them.
 */
export function Panel({
  title,
  aside,
  scrolls = true,
  children,
}: {
  title: string;
  aside?: React.ReactNode;
  scrolls?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className="flex min-h-0 min-w-0 flex-col">
      <header className="hairline flex items-center justify-between gap-3 px-5 py-3">
        <Eyebrow>{title}</Eyebrow>
        {aside ? (
          <span className="text-faint shrink-0 font-mono text-[11px]">
            {aside}
          </span>
        ) : null}
      </header>
      <div
        className={`min-h-0 min-w-0 flex-1 px-5 py-4 ${
          scrolls ? "overflow-y-auto" : "overflow-hidden"
        }`}
      >
        {children}
      </div>
    </section>
  );
}
