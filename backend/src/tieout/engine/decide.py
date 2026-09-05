"""What Tieout proposes, and when it refuses to propose anything at all.

The confidence is not a feeling and it is not a number a language model produced. Each class
of exception has a written checklist; each line either passes or it does not; the confidence
is the weight that passed. A judge can read the checklist and predict the number.

Two ways to end up refusing, and both are first-class outcomes rather than errors:

* the confidence is below ``CONFIDENCE_FLOOR``; or
* a **required** check failed — the one thing that class cannot be decided without.

The model's only job here is to write the paragraph that explains a decision the code has
already made. If it is unavailable, the code writes the paragraph itself and says so.
"""

from __future__ import annotations

from datetime import date, datetime

from . import model as llm
from .models import (
    Check,
    Decision,
    DecisionAction,
    EvidencePack,
    ExceptionCase,
    ExceptionKind,
    Fact,
    FactKind,
)

# Below this, Tieout stops and asks a person. Named, so nobody has to guess where it lives.
CONFIDENCE_FLOOR = 0.70

# Finance tolerances. Not magic numbers: these are the AP team's stated thresholds.
PRICE_VARIANCE_TOLERANCE_PCT = 5.0
SHORT_SHIP_TOLERANCE_PCT = 10.0

# The check each class cannot be decided without, whatever the rest of the score says.
REQUIRED_CHECK: dict[ExceptionKind, str] = {
    ExceptionKind.SHORT_SHIP: "the supplier's own document agrees with the warehouse",
    ExceptionKind.PRICE_VARIANCE: "the price variance is inside tolerance",
    ExceptionKind.MISSING_PO: "exactly one open order fits this invoice",
}

ACTION_FOR: dict[ExceptionKind, DecisionAction] = {
    ExceptionKind.SHORT_SHIP: DecisionAction.SHORT_PAY,
    ExceptionKind.PRICE_VARIANCE: DecisionAction.APPROVE,
    ExceptionKind.MISSING_PO: DecisionAction.ATTACH_PO,
    ExceptionKind.UNKNOWN: DecisionAction.REFUSE,
}


# --------------------------------------------------------------------------------------
# The checklists
# --------------------------------------------------------------------------------------


def checklist(case: ExceptionCase, facts: list[Fact]) -> list[Check]:
    """The deterministic checklist for this class of exception."""
    if case.kind is ExceptionKind.SHORT_SHIP:
        return _short_ship_checks(case, facts)
    if case.kind is ExceptionKind.PRICE_VARIANCE:
        return _price_variance_checks(case, facts)
    if case.kind is ExceptionKind.MISSING_PO:
        return _missing_po_checks(case, facts)
    return _unknown_checks(case, facts)


def _has(facts: list[Fact], kind: FactKind) -> bool:
    return any(fact.kind == kind for fact in facts)


def _first(facts: list[Fact], kind: FactKind) -> Fact | None:
    return next((fact for fact in facts if fact.kind == kind), None)


def _short_ship_checks(case: ExceptionCase, facts: list[Fact]) -> list[Check]:
    note = _first(facts, FactKind.DELIVERY_NOTE)
    shipped = note.figures.qty_shipped if note else None
    agrees = shipped is not None and shipped == case.qty_received
    return [
        Check(
            name="the purchase order is on file",
            passed=_has(facts, FactKind.PURCHASE_ORDER),
            weight=0.15,
            detail=f"order {case.po_id}" if case.po_id else "no order number",
        ),
        Check(
            name="the warehouse booked the goods in",
            passed=_has(facts, FactKind.GOODS_RECEIPT),
            weight=0.20,
            detail=f"{case.qty_received} of {case.qty_billed} units received",
        ),
        Check(
            name="the supplier published a shipping document",
            passed=note is not None,
            weight=0.30,
            detail=(
                f"delivery note read on VendorLink ({shipped} shipped)"
                if note
                else "nothing on the supplier portal"
            ),
        ),
        Check(
            name=REQUIRED_CHECK[ExceptionKind.SHORT_SHIP],
            passed=agrees,
            weight=0.20,
            detail=(
                f"portal says {shipped} shipped, goods receipt says {case.qty_received} received"
                if shipped is not None
                else "no shipped quantity to compare"
            ),
        ),
        Check(
            name="the supplier confirmed the shortfall in writing",
            passed=_has(facts, FactKind.VENDOR_EMAIL),
            weight=0.15,
            detail=(
                "vendor email on the trail"
                if _has(facts, FactKind.VENDOR_EMAIL)
                else "no correspondence found"
            ),
        ),
    ]


def _price_variance_checks(case: ExceptionCase, facts: list[Fact]) -> list[Check]:
    variance = case.price_variance_pct
    return [
        Check(
            name="the purchase order price is on file",
            passed=_has(facts, FactKind.PURCHASE_ORDER),
            weight=0.20,
            detail=f"order {case.po_id}" if case.po_id else "no order number",
        ),
        Check(
            name="the quantity delivered matches the quantity billed",
            passed=_has(facts, FactKind.GOODS_RECEIPT) and case.qty_short == 0,
            weight=0.20,
            detail=f"{case.qty_received} received against {case.qty_billed} billed",
        ),
        Check(
            name=REQUIRED_CHECK[ExceptionKind.PRICE_VARIANCE],
            passed=variance <= PRICE_VARIANCE_TOLERANCE_PCT,
            weight=0.30,
            detail=f"{variance:.2f}% against a {PRICE_VARIANCE_TOLERANCE_PCT:g}% tolerance",
        ),
        Check(
            name="the supplier gave written notice of the increase",
            passed=_has(facts, FactKind.VENDOR_EMAIL),
            weight=0.30,
            detail=(
                "notice found in the AP mailbox"
                if _has(facts, FactKind.VENDOR_EMAIL)
                else "no notice found"
            ),
        ),
    ]


def _missing_po_checks(case: ExceptionCase, facts: list[Fact]) -> list[Check]:
    candidate = _first(facts, FactKind.CANDIDATE_PO)
    return [
        Check(
            name=REQUIRED_CHECK[ExceptionKind.MISSING_PO],
            passed=candidate is not None,
            weight=0.35,
            detail=(
                f"{case.po_id} is the only open order that fits"
                if candidate
                else "no single open order fits"
            ),
        ),
        Check(
            name="the amounts agree",
            passed=candidate is not None
            and candidate.figures.amount is not None
            and abs(candidate.figures.amount - case.amount) <= 0.01,
            weight=0.20,
            detail=f"invoice {case.amount:,.2f} {case.currency}",
        ),
        Check(
            name="the warehouse booked the goods in",
            passed=_has(facts, FactKind.GOODS_RECEIPT),
            weight=0.25,
            detail=(
                "goods receipt found against the candidate order"
                if _has(facts, FactKind.GOODS_RECEIPT)
                else "no goods receipt"
            ),
        ),
        Check(
            name="the correspondence names no other order",
            passed=_has(facts, FactKind.VENDOR_EMAIL),
            weight=0.20,
            detail=(
                "supplier's email reviewed"
                if _has(facts, FactKind.VENDOR_EMAIL)
                else "no correspondence found"
            ),
        ),
    ]


def _unknown_checks(case: ExceptionCase, facts: list[Fact]) -> list[Check]:
    return [
        Check(
            name="a purchase order exists",
            passed=_has(facts, FactKind.PURCHASE_ORDER) or _has(facts, FactKind.CANDIDATE_PO),
            weight=0.40,
            detail="nothing in the ERP authorises this spend"
            if not _has(facts, FactKind.PURCHASE_ORDER)
            else f"order {case.po_id}",
        ),
        Check(
            name="the warehouse booked something in",
            passed=_has(facts, FactKind.GOODS_RECEIPT),
            weight=0.30,
            detail="no goods receipt anywhere against this supplier",
        ),
        Check(
            name="the supplier explained the charge",
            passed=_has(facts, FactKind.VENDOR_EMAIL),
            weight=0.15,
            detail="no correspondence in the AP mailbox",
        ),
        Check(
            name="the supplier published a document",
            passed=_has(facts, FactKind.DELIVERY_NOTE),
            weight=0.15,
            detail="not on the supplier network",
        ),
    ]


def confidence(checks: list[Check]) -> float:
    total = sum(check.weight for check in checks)
    if not total:
        return 0.0
    passed = sum(check.weight for check in checks if check.passed)
    return round(passed / total, 2)


def complete(case: ExceptionCase, facts: list[Fact]) -> bool:
    """True when this class has everything it needs — the signal to stop investigating."""
    return all(check.passed for check in checklist(case, facts))


def required_check_passed(case: ExceptionCase, checks: list[Check]) -> bool:
    required = REQUIRED_CHECK.get(case.kind)
    if required is None:
        return False
    return any(check.name == required and check.passed for check in checks)


# --------------------------------------------------------------------------------------
# The proposal
# --------------------------------------------------------------------------------------


def propose(pack: EvidencePack, *, today: date | None = None) -> Decision:
    """Turn a sealed evidence pack into the decision Tieout wants a human to confirm."""
    today = today or date.today()
    case = pack.exception
    checks = checklist(case, pack.facts)
    score = confidence(checks)

    if score < CONFIDENCE_FLOOR or not required_check_passed(case, checks):
        return _refusal(pack, checks, score)

    action = ACTION_FOR[case.kind]
    summary, payable, attach = action_detail(case, action)
    rationale, rationale_by = _rationale(case, pack, checks, action, summary, today)
    return Decision(
        exception_id=case.id,
        action=action,
        summary=summary,
        rationale=rationale,
        rationale_by=rationale_by,
        confidence=score,
        checks=checks,
        auto=False,
        decided_at=datetime.now(),
        amount_payable=payable,
        attach_po=attach,
    )


def action_detail(
    case: ExceptionCase, action: DecisionAction
) -> tuple[str, float | None, str | None]:
    """The sentence, the money and the order number that go with each action."""
    if action is DecisionAction.SHORT_PAY:
        return (
            f"Short-pay {case.invoice_id} to the {case.qty_received} units actually received: "
            f"{case.supported_amount:,.2f} {case.currency} instead of {case.amount:,.2f}, "
            f"holding {case.exposure:,.2f}.",
            case.supported_amount,
            None,
        )
    if action is DecisionAction.APPROVE:
        return (
            f"Approve {case.invoice_id} in full at {case.amount:,.2f} {case.currency}: the "
            f"{case.price_variance_pct:.2f}% increase is inside the "
            f"{PRICE_VARIANCE_TOLERANCE_PCT:g}% tolerance and the supplier gave notice.",
            case.amount,
            None,
        )
    if action is DecisionAction.ATTACH_PO:
        return (
            f"Attach {case.po_id} to {case.invoice_id} and approve "
            f"{case.amount:,.2f} {case.currency}.",
            case.amount,
            case.po_id,
        )
    return (f"Refer {case.invoice_id} to a person.", None, None)


def _refusal(pack: EvidencePack, checks: list[Check], score: float) -> Decision:
    """Beat four. Not an error: an agent that knows the edge of what it knows."""
    case = pack.exception
    passed = sum(1 for check in checks if check.passed)
    failed = [check for check in checks if not check.passed]
    dead_ends = [step for step in pack.steps if not step.found]

    lines = [
        f"I am not confident about {case.invoice_id} from {case.vendor_name} "
        f"({case.amount:,.2f} {case.currency}). {passed} of {len(checks)} checks passed.",
        "Here is where I looked:",
    ]
    for step in pack.steps:
        mark = "found" if step.found else "nothing"
        lines.append(f"  - {step.action} — {mark}{f' ({step.note})' if step.note else ''}")
    if failed:
        lines.append("What is missing: " + "; ".join(check.name for check in failed) + ".")
    lines.append("You decide.")

    return Decision(
        exception_id=case.id,
        action=DecisionAction.REFUSE,
        summary=(
            f"Not confident: {passed} of {len(checks)} checks passed "
            f"({score:.0%}, floor {CONFIDENCE_FLOOR:.0%}). "
            f"{len(dead_ends)} of the {len(pack.steps)} places I looked held nothing."
        ),
        rationale="\n".join(lines),
        rationale_by="code",
        confidence=score,
        checks=checks,
        auto=False,
        decided_at=datetime.now(),
    )


def _rationale(
    case: ExceptionCase,
    pack: EvidencePack,
    checks: list[Check],
    action: DecisionAction,
    summary: str,
    today: date,
) -> tuple[str, str]:
    """The model drafts the prose. If it cannot, the code writes it and the trail says so."""
    try:
        drafted = llm.draft_rationale(
            case,
            pack.facts,
            checks,
            action=action.value,
            proposal=summary,
            today=today,
        )
    except llm.ModelError:
        return _rationale_from_checks(case, pack, checks, summary), "code"
    return drafted, llm.label()


def _rationale_from_checks(
    case: ExceptionCase, pack: EvidencePack, checks: list[Check], summary: str
) -> str:
    sources = ", ".join(source.value for source in pack.sources_used)
    passed = [check for check in checks if check.passed]
    return (
        f"{case.headline} Tieout checked {len(checks)} things across {sources} and "
        f"{len(passed)} passed: "
        + "; ".join(f"{check.name} ({check.detail})" for check in passed)
        + f". {summary}"
    )
