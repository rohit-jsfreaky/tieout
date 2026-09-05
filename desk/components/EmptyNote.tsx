/** What a zone says before a run has put anything in it. Quiet, not apologetic. */
export function EmptyNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-faint max-w-[34ch] text-[13px] leading-relaxed">
      {children}
    </p>
  );
}
