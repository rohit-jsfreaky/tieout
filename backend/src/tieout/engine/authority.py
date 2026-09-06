"""The delegation-of-authority matrix: who is allowed to sign off how much.

Every AP department has one of these. It is the control that stops one approval from being
an unbounded one, and it is the reason an invoice above a person's limit never reaches that
person's desk in the first place. Tieout treats it as part of the loop rather than as a
footnote, in two places:

* **A decision above the approver's limit is blocked**, not recorded. Escalating is a
  first-class outcome, exactly like refusing.
* **A learned rule inherits the ceiling of whoever approved it.** A Controller cannot create
  a rule that later clears a 50,000 invoice on its own. That is segregation of duties, and
  it is enforced in ``policy.covers`` rather than written down and hoped for.

``policy.py`` still owns rules. This file owns one question: may this person sign this?
"""

from __future__ import annotations

from .models import Approver, DecisionAction, ExceptionCase, Role

# --------------------------------------------------------------------------------------
# THE DELEGATION-OF-AUTHORITY MATRIX
#
# Who may approve how much, in the invoice currency. Every finance team already has this
# table — in the ERP's approval workflow, or as a page in the finance manual — so a real
# deployment reads it from the company's own policy rather than from this file. It lives
# here as a named constant so that a reader can see the whole control in four lines.
#
# ``None`` means no limit.
# --------------------------------------------------------------------------------------
AUTHORITY_LIMITS: dict[Role, float | None] = {
    Role.AP_CLERK: 1_000.00,
    Role.CONTROLLER: 10_000.00,
    Role.CFO: None,
}

# Lowest authority first. The order the matrix is escalated up.
LADDER: tuple[Role, ...] = (Role.AP_CLERK, Role.CONTROLLER, Role.CFO)

# "an AP Clerk", "a Controller". How the title is said out loud decides this, not its first
# letter, so it is a table rather than a rule.
ARTICLE: dict[Role, str] = {
    Role.AP_CLERK: "an",
    Role.CONTROLLER: "a",
    Role.CFO: "a",
}

# What a person may type instead of the exact title.
ROLE_ALIASES: dict[str, Role] = {
    "ap clerk": Role.AP_CLERK,
    "ap-clerk": Role.AP_CLERK,
    "clerk": Role.AP_CLERK,
    "accounts payable clerk": Role.AP_CLERK,
    "controller": Role.CONTROLLER,
    "financial controller": Role.CONTROLLER,
    "cfo": Role.CFO,
    "chief financial officer": Role.CFO,
}


class UnknownRole(ValueError):
    """Tieout will not guess what somebody is allowed to approve."""


# --------------------------------------------------------------------------------------
# Reading the matrix
# --------------------------------------------------------------------------------------


def limit_for(role: Role) -> float | None:
    """The most this role may approve for payment. ``None`` means no limit."""
    return AUTHORITY_LIMITS[role]


def describe_limit(role: Role) -> str:
    limit = limit_for(role)
    return "no limit" if limit is None else f"{limit:,.2f}"


def against_limit(role: Role) -> str:
    """The clause a decision's rationale ends with, in English rather than in a format string."""
    limit = limit_for(role)
    return "with no approval limit" if limit is None else f"against a {limit:,.2f} limit"


def within_limit(role: Role, amount: float) -> bool:
    limit = limit_for(role)
    return limit is None or amount <= limit


def role_needed_for(amount: float) -> Role:
    """The lowest role in the matrix that may sign this amount off."""
    for role in LADDER:
        if within_limit(role, amount):
            return role
    return LADDER[-1]


def amount_under_authority(case: ExceptionCase, action: DecisionAction) -> float:
    """The money the approver is actually authorising to leave the company.

    This is a real accounting distinction and it is the one to get right: authority is
    measured on the amount being approved **for payment**, not on the invoice's face value
    and not on the exception's exposure.

    * ``short_pay`` — the short-paid amount, because that is the payment that gets made.
      Holding 92.50 back from a 1,850.00 invoice authorises 1,757.50, not 1,850.00.
    * ``approve`` and ``attach_po`` — the invoice total, because the whole invoice is paid.
    * ``reject`` — nothing is paid, so saying no needs no spending authority.
    * ``refuse`` and ``escalate`` — nothing has been agreed, so the whole invoice is still
      on the table and the total is what a person would have to sign for.
    """
    if action is DecisionAction.SHORT_PAY:
        return case.supported_amount
    if action is DecisionAction.REJECT:
        return 0.0
    return case.amount


# --------------------------------------------------------------------------------------
# Who is deciding
# --------------------------------------------------------------------------------------


def parse_role(text: str) -> Role:
    """``"Controller"``, ``"cfo"``, ``"AP Clerk"`` — anything the matrix recognises."""
    key = " ".join(text.strip().lower().split())
    if key in ROLE_ALIASES:
        return ROLE_ALIASES[key]
    raise UnknownRole(
        f"'{text.strip()}' is not a role in the delegation-of-authority matrix. "
        f"It has {', '.join(role.value for role in LADDER)}."
    )


def approver_for(by: str, role: str | Role | None = None) -> Approver:
    """Build the approver from a name and a role, or from ``"Chris, Controller"``.

    The role is never inferred and never defaulted: a decision whose authority nobody can
    check is worth less than no decision at all.
    """
    name = by.strip()
    if not name:
        raise UnknownRole("A decision needs a name on it.")

    if role is not None:
        resolved = role if isinstance(role, Role) else parse_role(str(role))
        return Approver(name=_without_role(name), role=resolved)

    head, comma, tail = name.rpartition(",")
    if not comma:
        raise UnknownRole(
            f"Tieout does not know what {name} is allowed to approve. Give a role — "
            f'{", ".join(role.value for role in LADDER)} — or write it as "{name}, Controller".'
        )
    return Approver(name=head.strip() or name, role=parse_role(tail))


def _without_role(name: str) -> str:
    """``"Chris, Controller"`` with an explicit role given is just ``"Chris"``."""
    head, comma, tail = name.rpartition(",")
    if not comma:
        return name
    try:
        parse_role(tail)
    except UnknownRole:
        return name
    return head.strip() or name


# --------------------------------------------------------------------------------------
# The sentence a blocked approval is told
# --------------------------------------------------------------------------------------


def over_limit_sentence(role: Role, amount: float, currency: str) -> str:
    """Plain English, and the same words on the screen, in the terminal and on the trail."""
    return (
        f"{amount:,.2f} {currency} is above {ARTICLE[role]} {role.value}'s "
        f"{describe_limit(role)} limit. This needs the {role_needed_for(amount).value}."
    )
