"use client";

import { CaretRight, CheckCircle } from "@phosphor-icons/react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { QueueRow } from "@/lib/api-types";
import { exceptionKindLabel, money } from "@/lib/format";

import { StatusBadge } from "./StatusBadge";

/**
 * The exceptions, and nothing else. The clean 87% of invoices never appear here.
 *
 * The blue line under a cleared row is the whole product on screen: a rule, and
 * the name of the person whose one approval created it.
 */
export function QueueTable({
  queue,
  selectedId,
  runningId,
  loading,
  onSelect,
}: {
  queue: QueueRow[];
  selectedId: string | null;
  runningId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-16">ID</TableHead>
          <TableHead>Class</TableHead>
          <TableHead>Invoice</TableHead>
          <TableHead className="text-right">Billed</TableHead>
          <TableHead className="text-right">At stake</TableHead>
          <TableHead className="text-right">Facts</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-8" />
        </TableRow>
      </TableHeader>

      <TableBody>
        {loading
          ? Array.from({ length: 5 }, (_, index) => (
              <TableRow key={index}>
                <TableCell colSpan={8}>
                  <Skeleton className="h-6 w-full" />
                </TableCell>
              </TableRow>
            ))
          : queue.map((row) => {
              const { exception, decision } = row;
              const running = exception.id === runningId || row.running;
              const cleared =
                decision?.auto === true && decision.cited_policy !== null;

              return [
                <TableRow
                  key={exception.id}
                  onClick={() => onSelect(exception.id)}
                  data-state={exception.id === selectedId ? "selected" : undefined}
                  className={cleared ? "cursor-pointer border-b-0" : "cursor-pointer"}
                >
                  <TableCell className="font-mono font-medium">
                    {exception.id}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {exceptionKindLabel(exception.kind)}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[22rem] truncate">
                    <span className="font-mono">{exception.invoice_id}</span>
                    <span className="text-muted-foreground"> · {exception.vendor_name}</span>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {money(exception.amount, exception.currency)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {money(exception.exposure, exception.currency)}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-right font-mono">
                    {row.facts || "—"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={exception.status} running={running} />
                  </TableCell>
                  <TableCell>
                    <CaretRight
                      size={12}
                      weight="bold"
                      className="text-faint"
                      aria-hidden
                    />
                  </TableCell>
                </TableRow>,

                cleared ? (
                  <TableRow key={`${exception.id}-cleared`}>
                    <TableCell colSpan={8} className="pt-0">
                      <p className="animate-land bg-ledger/8 text-ledger flex items-center gap-1.5 rounded-sm px-2 py-1.5 text-[12px] font-medium">
                        <CheckCircle size={13} weight="fill" aria-hidden />
                        cleared by {decision?.cited_policy} ·{" "}
                        {decision?.approved_by} — nobody was asked
                      </p>
                    </TableCell>
                  </TableRow>
                ) : null,
              ];
            })}
      </TableBody>
    </Table>
  );
}
