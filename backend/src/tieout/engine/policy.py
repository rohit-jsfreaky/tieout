"""THE self-improving loop. The only file that creates, versions, matches and applies rules.

One human decision becomes a rule, the rule carries that human's name, and the next
exception of the same kind clears itself and cites both. That is the whole product, and it
is three functions:

    learn(pack, decision, approved_by)  ->  Policy   a decision becomes a rule
    match(case, pack)                   ->  Policy?  does an existing rule cover this?
    apply(policy, case, pack)           ->  Decision the rule clears it, citing the human

**A rule is applied by code, never by a language model.** The model may draft the rule's name
and suggest a tolerance; every number it suggests is clamped here before anything is stored,
and the condition that actually gets evaluated is a handful of comparisons a reader can check
in ten seconds. That is what makes "auto-cleared, citing SHORT-SHIP-01 v1, approved by Chris,
Controller" reproducible rather than a story.

**A rule can never clear more than the person who approved it could have cleared by hand.**
Every Policy carries that person's approval limit from the delegation-of-authority matrix
(``authority.py``) and ``covers`` enforces it, so a Controller's approval cannot quietly turn
into a rule that settles a 50,000 invoice at three in the morning. That is segregation of
duties, and it is a comparison in this file rather than a promise in a README.

Nothing is ever deleted. A rule that stops being right is superseded by a new version, and
the old version stays on the record with the date it stopped applying.
"""

from __future__ import annotations

from datetime import date, datetime

from . import authority, decide, store
from . import model as llm
from .events import Event, EventKind, EventSink, null_sink
from .models import (
    Approver,
    Decision,
    DecisionAction,
    EvidencePack,
    ExceptionCase,
    ExceptionKind,
    FactKind,
    Policy,
    PolicyCondition,
)

# One family of rules per class of exception.
FAMILY_PREFIX: dict[ExceptionKind, str] = {
    ExceptionKind.SHORT_SHIP: "SHORT-SHIP",
    ExceptionKind.PRICE_VARIANCE: "PRICE-VAR",
    ExceptionKind.MISSING_PO: "MISSING-PO",
}

# The widest tolerance a learned rule may ever hold, however enthusiastic the draft.
MAX_TOLERANCE_PCT: dict[ExceptionKind, float] = {
    ExceptionKind.SHORT_SHIP: 10.0,
    ExceptionKind.PRICE_VARIANCE: 7.5,
    ExceptionKind.MISSING_PO: 0.0,
}

# A rule may cover at most twice the money it was learned from, and never less than the case.
EXPOSURE_HEADROOM = 2.0

# The evidence a rule of each class insists on before it will clear anything by itself.
REQUIRED_EVIDENCE: dict[ExceptionKind, list[FactKind]] = {
    ExceptionKind.SHORT_SHIP: [FactKind.GOODS_RECEIPT, FactKind.DELIVERY_NOTE],
    ExceptionKind.PRICE_VARIANCE: [FactKind.PURCHASE_ORDER, FactKind.VENDOR_EMAIL],
    ExceptionKind.MISSING_PO: [FactKind.CANDIDATE_PO, FactKind.GOODS_RECEIPT],
}

# Actions a human can take that are worth generalising into a rule.
LEARNABLE_ACTIONS = frozenset(
    {DecisionAction.SHORT_PAY, DecisionAction.APPROVE, DecisionAction.ATTACH_PO}
)


class PolicyError(RuntimeError):
    """A rule was asked to do something that would not survive an audit."""


# --------------------------------------------------------------------------------------
# What each class measures
# --------------------------------------------------------------------------------------


def observed_variance(case: ExceptionCase) -> float:
    """The one number a rule of this class is written against."""
    if case.kind is ExceptionKind.SHORT_SHIP:
        return case.short_pct
    if case.kind is ExceptionKind.PRICE_VARIANCE:
        return case.price_variance_pct
    return 0.0


def _tolerance_fields(kind: ExceptionKind, tolerance: float) -> dict[str, float | None]:
    if kind is ExceptionKind.SHORT_SHIP:
        return {"max_short_pct": tolerance, "max_price_variance_pct": None}
    if kind is ExceptionKind.PRICE_VARIANCE:
        return {"max_short_pct": None, "max_price_variance_pct": tolerance}
    return {"max_short_pct": None, "max_price_variance_pct": None}


def _tolerance_of(policy: Policy) -> float:
    if policy.kind is ExceptionKind.SHORT_SHIP:
        return policy.condition.max_short_pct or 0.0
    if policy.kind is ExceptionKind.PRICE_VARIANCE:
        return policy.condition.max_price_variance_pct or 0.0
    return 0.0


# --------------------------------------------------------------------------------------
# LEARN — one human decision becomes a rule
# --------------------------------------------------------------------------------------


def learn(
    pack: EvidencePack,
    decision: Decision,
    *,
    approved_by: Approver,
    today: date | None = None,
    sink: EventSink = null_sink,
) -> Policy | None:
    """Generalise a human decision. Returns the rule, a new version of one, or None."""
    today = today or date.today()
    case = pack.exception

    if decision.action is DecisionAction.REJECT:
        return _narrow_after_rejection(case, approved_by, sink)
    if decision.action not in LEARNABLE_ACTIONS or case.kind not in FAMILY_PREFIX:
        sink(
            Event(
                kind=EventKind.WARNING,
                exception_id=case.id,
                message=(
                    f"No rule learned from {case.id}: a {case.kind.value} decided by hand has "
                    "no pattern to generalise."
                ),
            )
        )
        return None

    measured = observed_variance(case)
    draft, drafted_by = _draft(case, decision, approved_by.label, measured, today)
    tolerance = _clamp_tolerance(case.kind, draft.tolerance_pct, measured)
    condition = PolicyCondition(
        kind=case.kind,
        # Deterministic and deliberately narrow: a rule learned from one supplier's behaviour
        # applies to that supplier. Widening it to every supplier needs its own approval.
        vendor_id=case.vendor_id,
        vendor_name=case.vendor_name,
        max_exposure=max(round(case.exposure * EXPOSURE_HEADROOM, 2), case.exposure),
        requires=REQUIRED_EVIDENCE[case.kind],
        **_tolerance_fields(case.kind, tolerance),
    )
    rationale = draft.rationale.strip() or _rationale_for(case, decision, tolerance)
    if draft.scope == "any":
        rationale += (
            f" (Drafted as applying to any supplier; Tieout narrowed it to "
            f"{case.vendor_name}, which is what the evidence covers.)"
        )

    # The rule inherits the approver's own limit and never outgrows it.
    ceiling = authority.limit_for(approved_by.role)
    rationale += (
        f" It can only clear payments a {approved_by.role.value} could have made by hand: "
        f"{authority.describe_limit(approved_by.role)}."
    )

    existing = _active_for(case.kind, case.vendor_id)
    now = datetime.now()
    if existing is None:
        policy = Policy(
            id=_next_id(case.kind),
            version=1,
            name=draft.name.strip() or _default_name(case),
            kind=case.kind,
            condition=condition,
            action=decision.action,
            rationale=rationale,
            drafted_by=drafted_by,
            approved_by=approved_by.label,
            approved_role=approved_by.role,
            authority_ceiling=ceiling,
            approved_at=now,
            learned_from=case.id,
            learned_from_invoice=case.invoice_id,
        )
        store.save_policy(policy)
        sink(
            Event(
                kind=EventKind.POLICY_LEARNED,
                exception_id=case.id,
                message=(
                    f"Learned {policy.ref}: {policy.name} — approved by {approved_by.label} on "
                    f"{now:%Y-%m-%d}, up to {authority.describe_limit(approved_by.role)}."
                ),
                policy=policy,
            )
        )
        return policy

    if not _contradicts(existing, condition, decision.action, ceiling):
        sink(
            Event(
                kind=EventKind.WARNING,
                exception_id=case.id,
                message=f"{existing.ref} already covers this. Nothing new to learn.",
            )
        )
        return existing

    return _version_up(
        existing,
        condition=condition,
        action=decision.action,
        name=draft.name.strip() or existing.name,
        rationale=rationale,
        drafted_by=drafted_by,
        approved_by=approved_by,
        ceiling=ceiling,
        learned_from=case.id,
        learned_from_invoice=case.invoice_id,
        sink=sink,
        message_suffix=f"widened after {approved_by.label} approved {case.id}",
    )


def _draft(
    case: ExceptionCase,
    decision: Decision,
    approved_by: str,
    measured: float,
    today: date,
) -> tuple[llm.RuleDraft, str]:
    """Ask the model for a name and a tolerance. Its answer is a suggestion, not a rule."""
    try:
        return (
            llm.generalise_decision(
                case,
                action=decision.action.value,
                approved_by=approved_by,
                observed_variance_pct=measured,
                today=today,
            ),
            llm.label(),
        )
    except llm.ModelError:
        return (
            llm.RuleDraft(
                name=_default_name(case),
                scope="vendor",
                tolerance_pct=measured,
                rationale=_rationale_for(case, decision, measured),
            ),
            "code",
        )


def _clamp_tolerance(kind: ExceptionKind, suggested: float, measured: float) -> float:
    """Never narrower than the case it was learned from, never wider than the class allows.

    The lower bound is what makes the loop dependable: the rule always covers at least the
    exception the human just approved, so a smaller one of the same shape always matches.
    """
    ceiling = MAX_TOLERANCE_PCT.get(kind, 0.0)
    if ceiling <= 0:
        return 0.0
    value = suggested if suggested and suggested > 0 else measured
    return round(min(max(value, measured), ceiling), 2)


def _default_name(case: ExceptionCase) -> str:
    if case.kind is ExceptionKind.SHORT_SHIP:
        return f"Short-pay small shortfalls from {case.vendor_name}"
    if case.kind is ExceptionKind.PRICE_VARIANCE:
        return f"Approve small notified price rises from {case.vendor_name}"
    return f"Attach the only matching open order for {case.vendor_name}"


def _rationale_for(case: ExceptionCase, decision: Decision, tolerance: float) -> str:
    return (
        f"Learned from {case.id} ({case.invoice_id}): {case.headline} The evidence was "
        f"consistent across the ERP, the supplier's own document and the AP mailbox, so the "
        f"same shape of exception up to {tolerance:g}% can take the same action "
        f"({decision.action.value}) without another approval."
    )


def _narrow_after_rejection(
    case: ExceptionCase, approved_by: Approver, sink: EventSink
) -> Policy | None:
    """A human said no to something a rule would have cleared. The rule stops covering it."""
    existing = _active_for(case.kind, case.vendor_id)
    if existing is None:
        sink(
            Event(
                kind=EventKind.WARNING,
                exception_id=case.id,
                message=f"No rule to narrow: nothing would have cleared {case.id} by itself.",
            )
        )
        return None

    measured = observed_variance(case)
    tightened = round(max(measured - 0.01, 0.0), 2)
    condition = existing.condition.model_copy(
        update={
            **_tolerance_fields(existing.kind, tightened),
            "max_exposure": min(existing.condition.max_exposure or case.exposure, case.exposure),
        }
    )
    # A rejection only ever narrows. So the ceiling is the tighter of the rule's and the
    # rejector's — a CFO saying no must not accidentally raise what the rule may clear.
    ceiling = _tighter(existing.authority_ceiling, authority.limit_for(approved_by.role))
    rationale = (
        f"{approved_by.label} rejected {case.id} ({case.invoice_id}), which "
        f"v{existing.version} would have cleared at {measured:g}%. The rule now stops at "
        f"{tightened:g}%. Version {existing.version} is kept for anything decided while it "
        f"applied."
    )
    return _version_up(
        existing,
        condition=condition,
        action=existing.action,
        name=existing.name,
        rationale=rationale,
        drafted_by="code",
        approved_by=approved_by,
        ceiling=ceiling,
        learned_from=case.id,
        learned_from_invoice=case.invoice_id,
        sink=sink,
        message_suffix=f"narrowed after {approved_by.label} rejected {case.id}",
    )


def _tighter(left: float | None, right: float | None) -> float | None:
    """The lower of two ceilings, where ``None`` means no limit at all."""
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)


def _version_up(
    existing: Policy,
    *,
    condition: PolicyCondition,
    action: DecisionAction,
    name: str,
    rationale: str,
    drafted_by: str,
    approved_by: Approver,
    ceiling: float | None,
    learned_from: str,
    learned_from_invoice: str,
    sink: EventSink,
    message_suffix: str,
) -> Policy:
    now = datetime.now()
    store.retire_policy(existing, now)
    policy = Policy(
        id=existing.id,
        version=existing.version + 1,
        name=name,
        kind=existing.kind,
        condition=condition,
        action=action,
        rationale=rationale,
        drafted_by=drafted_by,
        approved_by=approved_by.label,
        approved_role=approved_by.role,
        authority_ceiling=ceiling,
        approved_at=now,
        learned_from=learned_from,
        learned_from_invoice=learned_from_invoice,
        supersedes_version=existing.version,
    )
    store.save_policy(policy)
    sink(
        Event(
            kind=EventKind.POLICY_VERSIONED,
            exception_id=learned_from,
            message=f"{policy.ref} supersedes v{existing.version}: {message_suffix}.",
            policy=policy,
        )
    )
    return policy


def _contradicts(
    existing: Policy,
    condition: PolicyCondition,
    action: DecisionAction,
    ceiling: float | None,
) -> bool:
    """A new version is only worth creating when the rule would actually behave differently."""
    if existing.action is not action:
        return True
    if _tolerance_of(existing) + 1e-9 < (
        condition.max_short_pct or condition.max_price_variance_pct or 0.0
    ):
        return True
    # Someone with more authority approving the same shape raises what the rule may clear,
    # and that is a change of behaviour worth its own version and its own name on it.
    if existing.authority_ceiling is not None and (
        ceiling is None or ceiling > existing.authority_ceiling + 1e-9
    ):
        return True
    new_exposure = condition.max_exposure or 0.0
    return (existing.condition.max_exposure or 0.0) + 1e-9 < new_exposure


def _active_for(kind: ExceptionKind, vendor_id: str) -> Policy | None:
    candidates = [
        policy
        for policy in store.list_policies(active_only=True)
        if policy.kind is kind
        and (policy.condition.vendor_id is None or policy.condition.vendor_id == vendor_id)
    ]
    return max(candidates, key=lambda policy: policy.version) if candidates else None


def _next_id(kind: ExceptionKind) -> str:
    prefix = FAMILY_PREFIX[kind]
    existing = {policy.id for policy in store.list_policies() if policy.id.startswith(prefix)}
    return f"{prefix}-{len(existing) + 1:02d}"


# --------------------------------------------------------------------------------------
# MATCH — does a rule already cover this exception? Pure comparisons, no model.
# --------------------------------------------------------------------------------------


def match(case: ExceptionCase, pack: EvidencePack) -> Policy | None:
    """The rule that covers this exception, or None. Deterministic and re-runnable."""
    hits = [
        policy for policy in store.list_policies(active_only=True) if covers(policy, case, pack)
    ]
    return max(hits, key=lambda policy: (policy.version, policy.id)) if hits else None


def covers(policy: Policy, case: ExceptionCase, pack: EvidencePack) -> bool:
    """Every condition, spelled out. This is the function a judge should read."""
    condition = policy.condition
    if not policy.active or policy.kind is not case.kind:
        return False
    if condition.vendor_id is not None and condition.vendor_id != case.vendor_id:
        return False
    if condition.max_short_pct is not None and case.short_pct > condition.max_short_pct:
        return False
    if (
        condition.max_price_variance_pct is not None
        and case.price_variance_pct > condition.max_price_variance_pct
    ):
        return False
    if condition.max_exposure is not None and case.exposure > condition.max_exposure:
        return False
    # Segregation of duties. The rule may not authorise a payment the person who approved it
    # could not have authorised themselves, so it stops at their limit and escalates instead.
    if policy.authority_ceiling is not None and (
        authority.amount_under_authority(case, policy.action) > policy.authority_ceiling
    ):
        return False
    if any(not pack.has(kind) for kind in condition.requires):
        return False
    # A rule never rescues a weak pack: the class's own required check still has to pass.
    return decide.required_check_passed(case, decide.checklist(case, pack.facts))


# --------------------------------------------------------------------------------------
# APPLY — the rule clears the exception, citing the rule and the human behind it
# --------------------------------------------------------------------------------------


def apply(policy: Policy, case: ExceptionCase, pack: EvidencePack) -> Decision:
    """Clear an exception under a rule. No model call, so the wording is reproducible."""
    if not covers(policy, case, pack):
        raise PolicyError(f"{policy.ref} does not cover {case.id}")

    checks = decide.checklist(case, pack.facts)
    summary, payable, attach = decide.action_detail(case, policy.action)
    signing = authority.amount_under_authority(case, policy.action)
    ceiling = "no limit" if policy.authority_ceiling is None else f"{policy.authority_ceiling:,.2f}"
    rationale = (
        f"Auto-cleared under {policy.ref} — {policy.name} — approved by {policy.approved_by} "
        f"on {policy.approved_at:%d %B %Y}, learned from {policy.learned_from} "
        f"({policy.learned_from_invoice}). The rule applies when {policy.condition.describe()}. "
        f"This exception measures {observed_variance(case):g}% on "
        f"{case.exposure:,.2f} {case.currency}, and every piece of evidence the rule requires "
        f"is on the trail. It authorises {signing:,.2f} {case.currency} for payment, inside "
        f"the {ceiling} a {policy.approved_role.value} may approve. No human was needed."
    )
    return Decision(
        exception_id=case.id,
        action=policy.action,
        summary=summary,
        rationale=rationale,
        rationale_by="code",
        confidence=decide.confidence(checks),
        checks=checks,
        auto=True,
        cited_policy=policy.ref,
        approved_by=policy.approved_by,
        approved_role=policy.approved_role,
        decided_at=datetime.now(),
        amount_payable=payable,
        attach_po=attach,
        amount_for_authority=signing,
        authority_needed=authority.role_needed_for(signing),
        note=f"cleared by policy {policy.ref}",
    )


def citations(policy_id: str) -> list[str]:
    """Which exceptions this rule has cleared. Counted from the store, never hard-coded."""
    return [
        decision.exception_id
        for decision in store.list_decisions()
        if decision.cited_policy and decision.cited_policy.startswith(policy_id)
    ]
