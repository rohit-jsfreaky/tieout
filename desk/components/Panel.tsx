import { Eyebrow } from "./Eyebrow";

/** One of the three zones: a titled column that scrolls on its own so the
 *  counters and the controls never leave the screen. */
export function Panel({
  title,
  aside,
  children,
}: {
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="flex min-h-0 flex-col">
      <header className="hairline flex items-center justify-between px-5 py-3">
        <Eyebrow>{title}</Eyebrow>
        {aside ? (
          <span className="text-faint font-mono text-[11px]">{aside}</span>
        ) : null}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
    </section>
  );
}
