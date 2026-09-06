"use client";

import { ArrowCounterClockwise, Play } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Spinner } from "@/components/ui/spinner";
import type { Desk, View } from "@/lib/useDesk";

const TITLE: Record<View, { title: string; line: string }> = {
  queue: {
    title: "Queue",
    line: "The exceptions from a live three-way match. The clean invoices never reach this desk.",
  },
  exception: {
    title: "Exception",
    line: "What Tieout found, where it found it, and what it wants to do about it.",
  },
  policies: {
    title: "Policies",
    line: "Every rule Tieout learned, and the person whose approval created it.",
  },
  audit: {
    title: "Audit",
    line: "Every fact and every decision in the order they happened, with a source and a time.",
  },
  settings: {
    title: "Settings",
    line: "Who approves, where the API is, and how to put the world back.",
  },
};

/** The bar that is always there: where you are, and the two things you can do. */
export function DeskHeader({ desk }: { desk: Desk }) {
  const { title, line } = TITLE[desk.view];
  const busy = desk.pending !== null;

  return (
    <header className="hairline flex shrink-0 items-center gap-3 px-6 py-4">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />

      <div className="min-w-0">
        <h2 className="font-display text-[17px] leading-none font-[500]">
          {title}
        </h2>
        <p className="text-muted-foreground mt-1 truncate text-xs">{line}</p>
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <Button
          variant="outline"
          size="lg"
          onClick={desk.reset}
          disabled={busy}
          title="Put the world, the learned rules and the screenshots back to the seed"
        >
          {desk.pending === "reset" ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <ArrowCounterClockwise data-icon="inline-start" />
          )}
          Reset
        </Button>
        <Button
          size="lg"
          onClick={() => desk.nextId && desk.work(desk.nextId)}
          disabled={busy || desk.nextId === null}
        >
          {desk.pending === "work" ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <Play weight="fill" data-icon="inline-start" />
          )}
          {desk.nextId ? `Work next — ${desk.nextId}` : "Nothing left to work"}
        </Button>
      </div>
    </header>
  );
}
