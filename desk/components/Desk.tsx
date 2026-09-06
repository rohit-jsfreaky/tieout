"use client";

import { useState } from "react";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { useDesk } from "@/lib/useDesk";

import { AppSidebar } from "./AppSidebar";
import { DeskHeader } from "./DeskHeader";
import { ErrorBanner } from "./ErrorBanner";
import { AuditView } from "./views/AuditView";
import { ExceptionView } from "./views/ExceptionView";
import { PoliciesView } from "./views/PoliciesView";
import { QueueView } from "./views/QueueView";
import { SettingsView } from "./views/SettingsView";

/**
 * The desk.
 *
 * A sidebar, a header that always offers the next action, and one view at a
 * time. Every value on it came from the API in this session; there is no mock
 * mode and no seeded number anywhere in this folder.
 *
 * The views are state rather than routes so that a run keeps streaming while
 * somebody wanders off to read the rules it just learned — `useDesk` is mounted
 * once, for the life of the screen.
 */
export function Desk() {
  const desk = useDesk();
  const [guide, setGuide] = useState(true);

  return (
    <SidebarProvider className="h-svh min-h-0 overflow-hidden">
      <AppSidebar desk={desk} />

      <SidebarInset className="min-h-0 overflow-hidden">
        <DeskHeader desk={desk} />

        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1440px] px-6 py-6">
            {desk.error ? (
              <div className="mb-4">
                <ErrorBanner
                  message={desk.error}
                  onDismiss={desk.dismissError}
                />
              </div>
            ) : null}

            {desk.view === "queue" ? (
              <QueueView
                desk={desk}
                guide={guide}
                onDismissGuide={() => setGuide(false)}
              />
            ) : null}
            {desk.view === "exception" ? <ExceptionView desk={desk} /> : null}
            {desk.view === "policies" ? <PoliciesView desk={desk} /> : null}
            {desk.view === "audit" ? <AuditView desk={desk} /> : null}
            {desk.view === "settings" ? <SettingsView desk={desk} /> : null}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
