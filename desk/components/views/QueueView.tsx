"use client";

import { Tray } from "@phosphor-icons/react";

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Badge } from "@/components/ui/badge";
import type { Desk } from "@/lib/useDesk";

import { CounterStrip } from "../CounterStrip";
import { GuideCard } from "../GuideCard";
import { MoneyStrip } from "../MoneyStrip";
import { QueueTable } from "../QueueTable";

/**
 * Where a judge lands.
 *
 * The money, then the counts, then the exceptions. Nothing else is on this view,
 * because the only question it has to answer is "what broke, what does it cost,
 * and what do I click".
 */
export function QueueView({
  desk,
  guide,
  onDismissGuide,
}: {
  desk: Desk;
  guide: boolean;
  onDismissGuide: () => void;
}) {
  const empty = !desk.loading && desk.queue.length === 0;

  return (
    <div className="flex flex-col gap-6">
      {guide ? (
        <GuideCard
          nextId={desk.nextId}
          busy={desk.pending !== null}
          onWorkNext={() => desk.nextId && desk.work(desk.nextId)}
          onDismiss={onDismissGuide}
        />
      ) : null}

      <div className="flex flex-col gap-2">
        <MoneyStrip queue={desk.queue} loading={desk.loading} />
        <CounterStrip metrics={desk.metrics} loading={desk.loading} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Exceptions</CardTitle>
          <CardDescription>
            A live three-way match across every open invoice. Only the ones that
            did not tie out are here.
          </CardDescription>
          <CardAction>
            <Badge variant="secondary" className="font-mono">
              {desk.loading ? "—" : desk.queue.length}
            </Badge>
          </CardAction>
        </CardHeader>

        <CardContent className="px-0">
          {empty ? (
            <Empty>
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <Tray />
                </EmptyMedia>
                <EmptyTitle>Nothing broke</EmptyTitle>
                <EmptyDescription>
                  Every open invoice agreed with its order and its goods receipt.
                  Clean invoices never reach this desk.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            <QueueTable
              queue={desk.queue}
              selectedId={desk.selectedId}
              runningId={desk.runningId}
              loading={desk.loading}
              onSelect={desk.select}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
