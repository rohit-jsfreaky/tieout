"use client";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AuthorityRow, Role } from "@/lib/api-types";
import { limitLabel } from "@/lib/format";

/**
 * The seat the person at the desk is sitting in.
 *
 * The options are the rows of `GET /authority` and nothing else: a seat this
 * screen offered that the engine's matrix did not hold would be a promise the
 * engine never made. Until the matrix lands there is one option — the seat
 * already chosen — and the control is disabled.
 */
export function RoleSelect({
  authority,
  value,
  disabled = false,
  id,
  className,
  onChange,
}: {
  authority: AuthorityRow[];
  value: Role;
  disabled?: boolean;
  id?: string;
  className?: string;
  onChange: (role: Role) => void;
}) {
  const seats = authority.length > 0 ? authority : [{ role: value, limit: null }];
  const items = seats.map((seat) => ({
    value: seat.role,
    label:
      authority.length > 0
        ? `${seat.role} · ${limitLabel(seat.limit)}`
        : seat.role,
  }));

  return (
    <Select
      items={items}
      value={value}
      disabled={disabled || authority.length === 0}
      onValueChange={(chosen) => onChange(chosen as Role)}
    >
      <SelectTrigger id={id} className={className}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {items.map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {item.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
