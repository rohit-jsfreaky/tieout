"""The counters, computed from the store. Nothing here is written by hand.

The one that matters is ``human_touches`` next to ``touches_avoided_by_policy``: one approval
from a person, and every later exception of that shape costs nobody anything. An approval is
one touch; an auto-clear is zero.

``worked`` and ``open_not_worked`` always add up to ``exceptions_found``, so the counters
never quietly lose the exceptions nobody has picked up yet.
"""

from __future__ import annotations

from . import policy, store
from .models import DecisionAction, ExceptionStatus, Metrics


def compute() -> Metrics:
    cases = store.list_exceptions()
    packs = store.list_packs()
    decisions = store.list_decisions()
    policies = store.list_policies()

    return Metrics(
        exceptions_found=len(cases),
        worked=len(packs),
        open_not_worked=sum(1 for case in cases if case.status is ExceptionStatus.OPEN),
        auto_cleared=sum(1 for decision in decisions if decision.auto),
        refused=sum(1 for case in cases if case.status is ExceptionStatus.REFUSED),
        awaiting_human=sum(
            1
            for case in cases
            # An escalation is waiting on a person too — just on a more senior one.
            if case.status
            in {
                ExceptionStatus.PROPOSED,
                ExceptionStatus.REFUSED,
                ExceptionStatus.ESCALATED,
            }
        ),
        human_touches=sum(
            1 for decision in decisions if not decision.auto and decision.approved_by
        ),
        touches_avoided_by_policy=sum(
            1
            for decision in decisions
            if decision.auto and decision.action is not DecisionAction.REFUSE
        ),
        evidence_items=sum(len(pack.facts) for pack in packs),
        screenshots=sum(1 for pack in packs for fact in pack.facts if fact.screenshot),
        policies_active=sum(1 for rule in policies if rule.active),
        policy_citations=sum(len(policy.citations(rule.id)) for rule in policies if rule.active),
    )
