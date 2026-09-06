"use client";

import { WarningCircle, X } from "@phosphor-icons/react";

import { Alert, AlertAction, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

/** What went wrong, in the API's own words. Never a spinner that never ends. */
export function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <Alert>
      <WarningCircle weight="bold" />
      <AlertTitle>Tieout could not do that</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
      <AlertAction>
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          <X />
        </Button>
      </AlertAction>
    </Alert>
  );
}
