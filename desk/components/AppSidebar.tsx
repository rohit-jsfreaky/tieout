"use client";

import {
  ClockCounterClockwise,
  FileMagnifyingGlass,
  Gear,
  Scales,
  Tray,
  type Icon,
} from "@phosphor-icons/react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import type { Desk, View } from "@/lib/useDesk";

interface Entry {
  view: View;
  label: string;
  icon: Icon;
  hint: string;
}

const DESK: Entry[] = [
  { view: "queue", label: "Queue", icon: Tray, hint: "The invoices that broke" },
  {
    view: "exception",
    label: "Exception",
    icon: FileMagnifyingGlass,
    hint: "The evidence pack and the decision",
  },
  {
    view: "policies",
    label: "Policies",
    icon: Scales,
    hint: "Rules learned from a person",
  },
  {
    view: "audit",
    label: "Audit",
    icon: ClockCounterClockwise,
    hint: "Every fact and decision, in order",
  },
];

/**
 * The navigation, and the shape of the product in five words.
 *
 * The order is the loop: what broke, what was found, what was learned, what can
 * be proved. Settings sits apart because nothing in the demo happens there.
 */
export function AppSidebar({ desk }: { desk: Desk }) {
  const badge = (view: View): string | null => {
    if (view === "queue") return desk.queue.length ? String(desk.queue.length) : null;
    if (view === "exception") return desk.selectedId;
    if (view === "policies")
      return desk.policies.length ? String(desk.policies.length) : null;
    if (view === "audit")
      return desk.metrics ? String(desk.metrics.evidence_items) : null;
    return null;
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="gap-0 px-3 py-4">
        <h1 className="font-display text-[19px] leading-none font-[500] tracking-[-0.01em] group-data-[collapsible=icon]:hidden">
          Tieout
        </h1>
        <p className="text-muted-foreground mt-1.5 text-xs leading-snug group-data-[collapsible=icon]:hidden">
          the invoices that broke, and nothing else
        </p>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Desk</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {DESK.map((entry) => {
                const Mark = entry.icon;
                const mark = badge(entry.view);
                return (
                  <SidebarMenuItem key={entry.view}>
                    <SidebarMenuButton
                      isActive={desk.view === entry.view}
                      tooltip={entry.hint}
                      onClick={() => desk.setView(entry.view)}
                    >
                      <Mark weight={desk.view === entry.view ? "fill" : "regular"} />
                      <span>{entry.label}</span>
                    </SidebarMenuButton>
                    {mark ? (
                      <SidebarMenuBadge className="font-mono">
                        {mark}
                      </SidebarMenuBadge>
                    ) : null}
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              isActive={desk.view === "settings"}
              tooltip="Approver, reset, API"
              onClick={() => desk.setView("settings")}
            >
              <Gear weight={desk.view === "settings" ? "fill" : "regular"} />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
