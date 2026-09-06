"use client";

import { useState } from "react";

import { ArrowCounterClockwise, FloppyDisk } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DEFAULT_API_BASE, apiBase, setApiBase } from "@/lib/api";
import { limitLabel } from "@/lib/format";
import type { Desk } from "@/lib/useDesk";

import { RoleSelect } from "../RoleSelect";

/**
 * The four things that are configuration rather than evidence.
 *
 * The approver's name and seat are here and on the decision card, because they
 * are the settings that end up written into the product's output — the name on
 * the rule, and the ceiling that rule can never exceed.
 */
export function SettingsView({ desk }: { desk: Desk }) {
  // Settings is only ever reached by clicking the sidebar, so this initialiser
  // runs in the browser and can read the stored override directly. The queue is
  // what the server renders.
  const [base, setBase] = useState(() => apiBase());
  const [saved, setSaved] = useState(true);

  const save = () => {
    setApiBase(base);
    setSaved(true);
    window.location.reload();
  };

  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Approver</CardTitle>
          <CardDescription>
            Whose name goes on a rule, and what that person is allowed to sign.
            Every exception a rule later clears cites this person, which is what
            makes an auto-clear auditable.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field orientation="responsive">
              <FieldLabel htmlFor="settings-approver">Name</FieldLabel>
              <Input
                id="settings-approver"
                value={desk.approver.name}
                onChange={(event) =>
                  desk.setApprover({ ...desk.approver, name: event.target.value })
                }
                placeholder="Chris"
                className="w-44"
              />
            </Field>
            <Field orientation="responsive">
              <FieldLabel htmlFor="settings-role">Seat</FieldLabel>
              <RoleSelect
                id="settings-role"
                authority={desk.authority}
                value={desk.approver.role}
                onChange={(role) => desk.setApprover({ ...desk.approver, role })}
              />
              <FieldDescription>
                {desk.approverSeat === null
                  ? "The matrix has not loaded, so this seat's limit is unknown — not unlimited."
                  : `May approve ${limitLabel(desk.approverSeat.limit)} · that ceiling goes on every rule this seat's approval creates.`}
              </FieldDescription>
            </Field>
          </FieldGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Delegation of authority</CardTitle>
          <CardDescription>
            {desk.authorityNote ||
              "Read from GET /authority — the desk never states a limit the engine did not publish."}
          </CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Seat</TableHead>
                <TableHead className="text-right">May approve up to</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {desk.authority.map((row) => (
                <TableRow
                  key={row.role}
                  data-state={
                    row.role === desk.approver.role ? "selected" : undefined
                  }
                >
                  <TableCell className="font-medium">{row.role}</TableCell>
                  <TableCell className="text-right font-mono">
                    {limitLabel(row.limit)}
                  </TableCell>
                </TableRow>
              ))}
              {desk.authority.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} className="text-muted-foreground">
                    The matrix has not loaded yet.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API</CardTitle>
          <CardDescription>
            The desk holds no logic. Every number, fact and rule on this screen
            came from this address in this session.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="settings-api">Base URL</FieldLabel>
              <Input
                id="settings-api"
                value={base}
                onChange={(event) => {
                  setBase(event.target.value);
                  setSaved(false);
                }}
                placeholder={DEFAULT_API_BASE}
                spellCheck={false}
                className="font-mono"
              />
              <FieldDescription>
                Defaults to <code className="font-mono">{DEFAULT_API_BASE}</code>{" "}
                from <code className="font-mono">NEXT_PUBLIC_API_BASE</code>.
                Saving reloads the desk against the new address; clear the field
                to go back to the default.
              </FieldDescription>
            </Field>
            <Button className="self-start" disabled={saved} onClick={save}>
              <FloppyDisk data-icon="inline-start" />
              Save and reload
            </Button>
          </FieldGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Reset the world</CardTitle>
          <CardDescription>
            Puts the fake company, the learned rules, the saved portal session and
            the screenshots back to the seed, so the demo can be run again from
            the top.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog>
            <DialogTrigger
              render={<Button variant="outline" disabled={desk.pending !== null} />}
            >
              {desk.pending === "reset" ? (
                <Spinner data-icon="inline-start" />
              ) : (
                <ArrowCounterClockwise data-icon="inline-start" />
              )}
              Reset
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Back to the seed?</DialogTitle>
                <DialogDescription>
                  Five exceptions return, every learned rule is forgotten, the
                  VendorLink session is signed out and the screenshots are
                  deleted. Nothing outside Tieout is touched.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose render={<Button variant="outline" />}>
                  Keep it as it is
                </DialogClose>
                <DialogClose render={<Button onClick={desk.reset} />}>
                  Reset everything
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
