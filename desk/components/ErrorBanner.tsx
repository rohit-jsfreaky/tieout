import { WarningCircle, X } from "@phosphor-icons/react";

/** What went wrong, in the API's own words. Never a spinner that never ends. */
export function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="hairline flex shrink-0 items-center gap-3 bg-mist px-6 py-2.5"
    >
      <WarningCircle size={15} weight="bold" className="shrink-0" aria-hidden />
      <p className="min-w-0 flex-1 text-[13px]">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss"
        className="text-faint hover:text-ink shrink-0"
      >
        <X size={13} weight="bold" aria-hidden />
      </button>
    </div>
  );
}
