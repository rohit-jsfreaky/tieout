"use client";

import {
  NumberCircleOne,
  NumberCircleThree,
  NumberCircleTwo,
  Play,
  X,
  type Icon,
} from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const STEPS: { mark: Icon; title: string; line: string }[] = [
  {
    mark: NumberCircleOne,
    title: "Work E1",
    line: "Watch it read the ERP, the mailbox and the supplier portal — signing in to the portal on camera, because that one has no API.",
  },
  {
    mark: NumberCircleTwo,
    title: "Approve it",
    line: "A rule is created with your name on it, stamped with today's date and the exception it was learned from.",
  },
  {
    mark: NumberCircleThree,
    title: "Work E2",
    line: "It clears itself, citing that rule. Nobody is asked. Human touches stays at one.",
  },
];

/**
 * Three minutes, no context: this is where you click.
 *
 * The demo has one shape and it is not obvious from a queue of five rows, so the
 * queue says it out loud until somebody dismisses it.
 */
export function GuideCard({
  nextId,
  busy,
  onWorkNext,
  onDismiss,
}: {
  nextId: string | null;
  busy: boolean;
  onWorkNext: () => void;
  onDismiss: () => void;
}) {
  return (
    <Card className="bg-soft">
      <CardHeader>
        <CardTitle className="font-display text-[17px] font-[500]">
          Three steps, and you have seen the whole thing
        </CardTitle>
        <CardDescription>
          Tieout ignores the invoices that tied out. These five broke — and after
          one of them is approved, the next of the same kind never reaches a
          person again.
        </CardDescription>
        <CardAction>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onDismiss}
            aria-label="Dismiss the guide"
          >
            <X />
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <ol className="grid gap-3 md:grid-cols-3">
          {STEPS.map((step) => {
            const Mark = step.mark;
            return (
              <li key={step.title} className="flex gap-2.5">
                <Mark
                  size={18}
                  weight="fill"
                  className="text-ledger mt-px shrink-0"
                  aria-hidden
                />
                <div className="min-w-0">
                  <p className="text-[13px] font-medium">{step.title}</p>
                  <p className="text-muted-foreground mt-0.5 text-xs leading-relaxed">
                    {step.line}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={onWorkNext} disabled={busy || nextId === null}>
            <Play weight="fill" data-icon="inline-start" />
            {nextId ? `Start here — work ${nextId}` : "Nothing left to work"}
          </Button>
          <span className="text-muted-foreground text-xs">
            Or open any row below to read its evidence pack first.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
