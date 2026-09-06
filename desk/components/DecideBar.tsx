"use client";

import { useState } from "react";

import { Check, PencilSimple, Prohibit } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import type { DecidableAction } from "@/lib/api-types";

/**
 * The one human touch.
 *
 * Approve means "do what Tieout proposed" — the engine resolves it into the real
 * action and records that. Edit is for the times it proposed the wrong thing:
 * pick what should happen instead and say why, in the same breath.
 *
 * The approver's name is on this card and not somewhere else, because it is
 * about to be stamped onto a rule that will clear invoices without asking again.
 */
const EDITS: { value: DecidableAction; label: string }[] = [
  { value: "short_pay", label: "Short-pay the difference" },
  { value: "attach_po", label: "Attach the purchase order" },
  { value: "approve", label: "Approve in full" },
  { value: "reject", label: "Reject the invoice" },
];

export function DecideBar({
  approver,
  setApprover,
  busy,
  disabled,
  onDecide,
}: {
  approver: string;
  setApprover: (name: string) => void;
  busy: boolean;
  disabled: boolean;
  onDecide: (action: DecidableAction, note: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [action, setAction] = useState<DecidableAction>("short_pay");
  const [note, setNote] = useState("");

  const send = (chosen: DecidableAction) => {
    onDecide(chosen, note.trim());
    setEditing(false);
    setNote("");
  };

  const stop = busy || disabled;
  const named = approver.trim();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your decision</CardTitle>
        <CardDescription>
          One click, once. Tieout learns the rule from it and stops asking.
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <FieldGroup>
          <Field orientation="responsive">
            <FieldLabel htmlFor="approver">Approver</FieldLabel>
            <Input
              id="approver"
              name="approver"
              value={approver}
              onChange={(event) => setApprover(event.target.value)}
              placeholder="Chris, Controller"
              className="sm:max-w-64"
            />
            <FieldDescription>
              This name goes on the rule, and every later auto-clear cites it.
            </FieldDescription>
          </Field>
        </FieldGroup>

        <Separator />

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ledger"
            size="lg"
            disabled={stop || named === ""}
            onClick={() => send("approve")}
          >
            {busy ? (
              <Spinner data-icon="inline-start" />
            ) : (
              <Check weight="bold" data-icon="inline-start" />
            )}
            Approve
          </Button>
          <Button
            variant="outline"
            size="lg"
            disabled={stop || named === ""}
            onClick={() => send("reject")}
          >
            <Prohibit data-icon="inline-start" />
            Reject
          </Button>
          <Button
            variant="outline"
            size="lg"
            disabled={stop}
            aria-expanded={editing}
            onClick={() => setEditing((open) => !open)}
          >
            <PencilSimple data-icon="inline-start" />
            Edit
          </Button>
          <span className="text-faint ml-auto text-[12px]">
            as {named || "— nobody —"}
          </span>
        </div>

        {editing ? (
          <FieldGroup className="animate-land">
            <Field>
              <FieldLabel htmlFor="instead">Do this instead</FieldLabel>
              <Select
                items={EDITS}
                value={action}
                onValueChange={(value) => setAction(value as DecidableAction)}
              >
                <SelectTrigger id="instead" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    {EDITS.map((edit) => (
                      <SelectItem key={edit.value} value={edit.value}>
                        {edit.label}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>

            <Field>
              <FieldLabel htmlFor="why">Why — this goes on the rule</FieldLabel>
              <Input
                id="why"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Northwind always ships the balance next week."
              />
            </Field>

            <Button
              size="lg"
              className="self-start"
              disabled={stop || named === ""}
              onClick={() => send(action)}
            >
              Record it
            </Button>
          </FieldGroup>
        ) : null}
      </CardContent>
    </Card>
  );
}
