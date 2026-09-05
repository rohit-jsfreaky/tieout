/** A small accented label. The accent colour appears here, on ticks, and on the
 *  winning number — nowhere else on the screen. */
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-ledger text-[11px] font-medium tracking-[0.14em] uppercase">
      {children}
    </span>
  );
}
