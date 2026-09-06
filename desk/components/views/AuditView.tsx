"use client";

import { Camera, ClockCounterClockwise, LinkSimple } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { clock, day, readerLabel } from "@/lib/format";
import type { AuditEntry, Desk } from "@/lib/useDesk";

import { SourceChip } from "../SourceChip";

const KIND: Record<AuditEntry["kind"], string> = {
  fact: "Fact",
  decision: "Decision",
  policy: "Rule",
};

/**
 * The audit trail, made browsable.
 *
 * Every fact Tieout observed, every decision it recorded and every rule it
 * learned, across every exception, in the order they happened. Each line carries
 * the timestamp the engine wrote on the object itself, so this page can be read
 * a year from now and still say who knew what, and when.
 */
export function AuditView({ desk }: { desk: Desk }) {
  if (desk.auditLoading && desk.audit.length === 0) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 6 }, (_, index) => (
          <Skeleton key={index} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (desk.audit.length === 0) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <ClockCounterClockwise />
          </EmptyMedia>
          <EmptyTitle>Nothing recorded yet</EmptyTitle>
          <EmptyDescription>
            Work an exception and every lookup, every fact and every decision
            lands here with its source and its time.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Everything, in order</CardTitle>
        <CardDescription>
          One line per fact, decision and rule — with where it came from, who read
          it, and when.
        </CardDescription>
        <CardAction>
          <Badge variant="secondary" className="font-mono">
            {desk.audit.length}
          </Badge>
        </CardAction>
      </CardHeader>

      <CardContent className="px-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-20">Time</TableHead>
              <TableHead className="w-24">Type</TableHead>
              <TableHead className="w-28">Exception</TableHead>
              <TableHead className="w-24">Source</TableHead>
              <TableHead>What</TableHead>
              <TableHead className="w-40">Read by</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>

          <TableBody>
            {desk.audit.map((entry) => (
              <TableRow key={entry.key}>
                <TableCell
                  className="text-muted-foreground font-mono text-[12px]"
                  title={`${day(entry.at)} ${clock(entry.at)}`}
                >
                  {clock(entry.at)}
                </TableCell>

                <TableCell>
                  <Badge
                    variant={
                      entry.kind === "policy"
                        ? "ledger"
                        : entry.kind === "decision"
                          ? "secondary"
                          : "outline"
                    }
                  >
                    {KIND[entry.kind]}
                  </Badge>
                </TableCell>

                <TableCell className="font-mono text-[12px]">
                  {entry.exceptionId}
                  <span className="text-faint"> · {entry.subject}</span>
                </TableCell>

                <TableCell>
                  {entry.source ? <SourceChip source={entry.source} /> : null}
                </TableCell>

                <TableCell className="max-w-0 text-[13px] whitespace-normal">
                  {entry.what}
                  {entry.auto ? (
                    <span className="text-ledger"> — no human needed</span>
                  ) : null}
                </TableCell>

                <TableCell className="text-muted-foreground text-[12px]">
                  {entry.kind === "fact" ? readerLabel(entry.by) : entry.by}
                </TableCell>

                <TableCell>
                  <span className="flex items-center gap-1.5">
                    {entry.locator && entry.kind === "fact" ? (
                      <a
                        href={entry.locator}
                        target="_blank"
                        rel="noreferrer"
                        title={entry.locator}
                        className="text-faint hover:text-ledger"
                      >
                        <LinkSimple size={13} weight="bold" aria-hidden />
                        <span className="sr-only">Open the source</span>
                      </a>
                    ) : null}
                    {entry.screenshot ? (
                      <Camera
                        size={13}
                        weight="bold"
                        className="text-faint"
                        aria-label="A screenshot was filed with this fact"
                      />
                    ) : null}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
