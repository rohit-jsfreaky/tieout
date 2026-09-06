import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AuthorityRow, PolicyRow, Role } from "@/lib/api-types";
import { limitLabel } from "@/lib/format";

/**
 * The delegation-of-authority matrix, on the page where it bites.
 *
 * Every limit here came from `GET /authority` — the engine's own constant. A
 * number an approval is blocked by, and a ceiling a learned rule inherits for
 * life, is not a number a frontend gets to type in. The third column is the
 * point of putting the matrix next to the rules: it says how much of the policy
 * book each seat is personally answerable for.
 *
 * Settings shows the same matrix as configuration — who you are, and what you
 * may sign. This one is evidence: which seat every rule above was signed at.
 */
export function AuthorityMatrix({
  authority,
  policies,
  seat,
}: {
  authority: AuthorityRow[];
  policies: PolicyRow[];
  seat: Role;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Seat</TableHead>
          <TableHead className="text-right">May approve up to</TableHead>
          <TableHead className="text-right">Rules signed here</TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        {authority.map((row) => {
          const signed = policies.filter(
            ({ policy }) => policy.approved_role === row.role,
          ).length;

          return (
            <TableRow
              key={row.role}
              data-state={row.role === seat ? "selected" : undefined}
            >
              <TableCell className="font-medium">
                {row.role}
                {row.role === seat ? (
                  <span className="text-faint text-[11px]"> · at the desk</span>
                ) : null}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {limitLabel(row.limit)}
              </TableCell>
              <TableCell
                className={`text-right font-mono tabular-nums ${
                  signed ? "text-ledger" : "text-faint"
                }`}
              >
                {signed}
              </TableCell>
            </TableRow>
          );
        })}

        {authority.length === 0 ? (
          <TableRow>
            <TableCell colSpan={3} className="text-muted-foreground">
              The matrix has not loaded yet.
            </TableCell>
          </TableRow>
        ) : null}
      </TableBody>
    </Table>
  );
}
