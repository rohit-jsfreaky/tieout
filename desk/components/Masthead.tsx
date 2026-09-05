/** The wordmark and the one line that says what this screen is for. */
export function Masthead() {
  return (
    <div className="flex items-baseline justify-between gap-6">
      <div className="flex items-baseline gap-3">
        <h1 className="font-display text-[22px] font-[500] tracking-[-0.01em]">
          Tieout
        </h1>
        <p className="text-muted text-[13px]">
          the invoices that broke, and nothing else
        </p>
      </div>
      <p className="text-faint font-mono text-[11px] tracking-[0.06em] uppercase">
        Accounts payable · exception desk
      </p>
    </div>
  );
}
