/**
 * A row of named figures — `label value`, in the mono, tabular.
 *
 * Every number on this screen is supposed to be nameable, so the label travels
 * with the figure rather than sitting in a column header somewhere above it.
 */
export function FigureRow({ children }: { children: React.ReactNode }) {
  return (
    <dl className="text-muted-foreground flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px]">
      {children}
    </dl>
  );
}

export function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt className="text-faint">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
