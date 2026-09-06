"use client";

import { Scales } from "@phosphor-icons/react";

import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import type { Desk } from "@/lib/useDesk";

import { PolicyCard } from "../PolicyCard";

/** Learned rules, each stamped with the person who approved it and the date. */
export function PoliciesView({ desk }: { desk: Desk }) {
  if (desk.policies.length === 0) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Scales />
          </EmptyMedia>
          <EmptyTitle>No rules yet</EmptyTitle>
          <EmptyDescription>
            The first one is born the moment a human approves a decision, and it
            carries their name. Work an exception and approve it.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="grid gap-3 lg:grid-cols-2 2xl:grid-cols-3">
      {desk.policies.map((row) => (
        <PolicyCard
          key={row.policy.ref}
          row={row}
          fresh={row.policy.ref === desk.learned}
        />
      ))}
    </div>
  );
}
