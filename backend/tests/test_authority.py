"""Approval authority. Who may sign what, and what a rule inherits from them.

Four things are proved here, and the third is the sharp one:

1. a Controller cannot approve above their 10,000 limit — the decision is blocked, not made;
2. a CFO can, because the matrix gives them no limit;
3. **a rule learned from a Controller never auto-clears above 10,000**, even when every other
   condition on it matches exactly. That is segregation of duties: one approval cannot become
   an unbounded one while nobody is looking;
4. authority is measured on the money that actually leaves — the short-paid amount on a
   short-pay, the invoice total on an approve.
"""

from __future__ import annotations

from conftest import chromium_or_skip
from tieout.engine import authority, policy, store
from tieout.engine import investigate as investigate_engine
from tieout.engine.models import DecisionAction, ExceptionStatus, LineDiscrepancy, Role

CONTROLLER = "Chris, Controller"
CFO = "Dana, CFO"
CLERK = "Sam, AP Clerk"


# --------------------------------------------------------------------------------------
# The matrix itself
# --------------------------------------------------------------------------------------


def test_the_matrix_is_the_three_seats_and_their_limits() -> None:
    assert authority.limit_for(Role.AP_CLERK) == 1_000.00
    assert authority.limit_for(Role.CONTROLLER) == 10_000.00
    assert authority.limit_for(Role.CFO) is None

    assert authority.role_needed_for(900.00) is Role.AP_CLERK
    assert authority.role_needed_for(1_757.50) is Role.CONTROLLER
    assert authority.role_needed_for(12_750.00) is Role.CFO


def test_the_approver_carries_a_role_not_only_a_name() -> None:
    parsed = authority.approver_for("Chris, Controller")
    assert parsed.name == "Chris"
    assert parsed.role is Role.CONTROLLER
    assert parsed.label == "Chris, Controller"

    # A name and a role given separately mean the same thing, however it is spelled.
    assert authority.approver_for("Chris", "controller") == parsed
    assert authority.approver_for("Chris, Controller", Role.CONTROLLER) == parsed

    # Tieout never guesses what somebody is allowed to approve.
    for bad in ("Chris", "Chris, Warehouse Supervisor", ""):
        try:
            authority.approver_for(bad)
        except authority.UnknownRole:
            continue
        raise AssertionError(f"{bad!r} should not have produced an approver")


def test_authority_is_measured_on_the_money_that_actually_leaves(cases) -> None:
    """A real accounting distinction: the payment, not the invoice's face value."""
    short_ship = cases["E1"]
    assert short_ship.amount == 1_850.00
    assert short_ship.supported_amount == 1_757.50

    # Short-paying authorises the short-paid amount ...
    assert (
        authority.amount_under_authority(short_ship, DecisionAction.SHORT_PAY)
        == short_ship.supported_amount
    )
    # ... approving in full authorises the whole invoice ...
    assert authority.amount_under_authority(short_ship, DecisionAction.APPROVE) == 1_850.00
    assert authority.amount_under_authority(cases["E4"], DecisionAction.ATTACH_PO) == 3_480.00
    # ... and saying no pays nothing, so it needs no spending authority.
    assert authority.amount_under_authority(short_ship, DecisionAction.REJECT) == 0.0


# --------------------------------------------------------------------------------------
# Deciding above your limit
# --------------------------------------------------------------------------------------


def test_a_controller_cannot_approve_above_ten_thousand(sources, cases) -> None:
    chromium_or_skip()
    investigate_engine.work(cases["E5"], sources)  # 12,750 from Ardent Systems

    decision, learned = investigate_engine.apply_human_decision(
        cases["E5"], action=DecisionAction.APPROVE, by=CONTROLLER
    )

    assert decision.action is DecisionAction.ESCALATE, "blocked, not quietly allowed"
    assert decision.amount_for_authority == 12_750.00
    assert decision.authority_needed is Role.CFO
    assert decision.approved_role is Role.CONTROLLER
    assert decision.amount_payable is None, "nothing is authorised for payment"
    assert "12,750.00 USD is above a Controller's 10,000.00 limit" in decision.summary
    assert "This needs the CFO." in decision.summary

    assert learned is None, "a blocked decision teaches nothing"
    assert store.list_policies() == []
    assert store.get_exception("E5").status is ExceptionStatus.ESCALATED


def test_a_cfo_can(sources, cases) -> None:
    chromium_or_skip()
    investigate_engine.work(cases["E5"], sources)

    decision, _ = investigate_engine.apply_human_decision(
        cases["E5"], action=DecisionAction.APPROVE, by=CFO
    )

    assert decision.action is DecisionAction.APPROVE
    assert decision.approved_by == CFO
    assert decision.approved_role is Role.CFO
    assert decision.amount_for_authority == 12_750.00
    assert store.get_exception("E5").status is ExceptionStatus.RESOLVED


def test_an_ap_clerk_is_stopped_by_the_same_control(sources, cases) -> None:
    """E1 short-pays 1,757.50 — inside a Controller's limit, above a clerk's 1,000."""
    chromium_or_skip()
    investigate_engine.work(cases["E1"], sources)

    blocked, _ = investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=CLERK
    )
    assert blocked.action is DecisionAction.ESCALATE
    assert blocked.authority_needed is Role.CONTROLLER
    assert "above an AP Clerk's 1,000.00 limit" in blocked.summary

    # And the Controller above them signs the very same pack off without another look.
    allowed, learned = investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=CONTROLLER
    )
    assert allowed.action is DecisionAction.SHORT_PAY
    assert learned is not None


# --------------------------------------------------------------------------------------
# THE ONE THAT MATTERS — a rule cannot outgrow the person who approved it
# --------------------------------------------------------------------------------------


def _scaled_to(case, *, billed: int, received: int, unit_price: float):
    """The same exception shape at a bigger number: same supplier, same class, more money.

    Every dimension the rule is written against is deliberately kept well inside its own
    condition — the shortfall stays tiny and so does the exposure — so the only thing that
    can stop the rule clearing it is the ceiling.
    """
    line = case.lines[0]
    return case.model_copy(
        update={
            "id": "E1-BIG",
            "invoice_id": "INV-9999",
            "amount": round(billed * unit_price, 2),
            "lines": [
                LineDiscrepancy(
                    line_no=line.line_no,
                    sku=line.sku,
                    description=line.description,
                    qty_billed=billed,
                    qty_received=received,
                    qty_ordered=billed,
                    unit_price_billed=unit_price,
                    unit_price_ordered=unit_price,
                )
            ],
        }
    )


def test_a_rule_learned_from_a_controller_never_clears_above_their_limit(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.work(cases["E1"], sources)
    investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=CONTROLLER
    )
    rule = store.list_policies(active_only=True)[0]
    assert rule.approved_role is Role.CONTROLLER
    assert rule.authority_ceiling == 10_000.00

    # The same supplier, the same class, a shortfall and an exposure well inside the rule —
    # but 11,988.00 of payment, which Chris could never have signed off by hand.
    big = _scaled_to(cases["E1"], billed=1_000, received=999, unit_price=12.00)
    assert big.short_pct <= rule.condition.max_short_pct
    assert big.exposure <= rule.condition.max_exposure
    assert big.supported_amount == 11_988.00

    note = next(fact for fact in pack.facts if fact.kind.value == "delivery_note")
    big_pack = pack.model_copy(
        update={
            "exception": big,
            # The supplier's own document has to agree with the warehouse, or the required
            # check fails for an unrelated reason and this test proves nothing.
            "facts": [
                fact.model_copy(
                    update={"figures": fact.figures.model_copy(update={"qty_shipped": 999})}
                )
                if fact.id == note.id
                else fact
                for fact in pack.facts
            ],
        }
    )

    assert policy.covers(rule, big, big_pack) is False
    assert policy.match(big, big_pack) is None

    # Everything else about it does match: lift the ceiling and the very same rule covers it.
    assert policy.covers(rule.model_copy(update={"authority_ceiling": None}), big, big_pack)


def test_a_cfos_approval_widens_the_ceiling_into_a_new_version(sources, cases) -> None:
    """The way a rule's ceiling is raised is the way everything else changes: a new version."""
    chromium_or_skip()
    investigate_engine.work(cases["E1"], sources)
    investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=CONTROLLER
    )
    first = store.list_policies(active_only=True)[0]
    assert first.version == 1

    _, widened = investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=CFO
    )
    assert widened is not None
    assert widened.version == 2
    assert widened.supersedes_version == 1
    assert widened.approved_by == CFO
    assert widened.authority_ceiling is None, "a CFO's rule has no ceiling"
    assert store.get_policy(first.id, 1).active is False, "v1 is kept, on the record"
