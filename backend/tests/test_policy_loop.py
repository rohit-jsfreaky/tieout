"""THE test. One approval, and the next exception of that kind clears itself.

If this file is green, the product works: a human decided once, a rule was born with that
human's name on it, and the second short-ship was settled by code that cites both. Everything
else in Tieout exists to make this file true.
"""

from __future__ import annotations

from conftest import chromium_or_skip
from tieout.engine import investigate as investigate_engine
from tieout.engine import metrics, policy, store
from tieout.engine.models import DecisionAction, ExceptionKind, Role

APPROVER = "Chris, Controller"


def test_approve_once_and_the_next_one_clears_itself(sources, cases) -> None:
    chromium_or_skip()

    # Beat 1 — the first short ship is investigated and escalated to a person.
    first = investigate_engine.work(cases["E1"], sources)
    assert first.proposal is not None
    assert first.proposal.action is DecisionAction.SHORT_PAY
    assert first.proposal.auto is False
    assert first.proposal.confidence == 1.0
    assert store.list_policies() == []

    # Beat 2 — the person approves, and a rule is born with their name and the date on it.
    decision, learned = investigate_engine.apply_human_decision(
        cases["E1"], action=DecisionAction.APPROVE, by=APPROVER
    )
    assert decision.action is DecisionAction.SHORT_PAY
    assert decision.approved_by == APPROVER
    assert learned is not None
    assert learned.id == "SHORT-SHIP-01"
    assert learned.version == 1
    assert learned.approved_by == APPROVER
    assert learned.approved_role is Role.CONTROLLER
    # And it inherits his ceiling: the rule may never clear more than Chris could by hand.
    assert learned.authority_ceiling == 10_000.00
    assert learned.approved_at.date() is not None
    assert learned.learned_from == "E1"
    assert learned.kind is ExceptionKind.SHORT_SHIP
    assert learned.condition.vendor_id == cases["E1"].vendor_id
    # The rule always covers at least the case it was learned from.
    assert learned.condition.max_short_pct >= cases["E1"].short_pct

    # Beat 3 — the second short ship never reaches a person.
    second = investigate_engine.work(cases["E2"], sources)
    assert second.proposal is not None
    assert second.proposal.auto is True
    assert second.proposal.cited_policy == "SHORT-SHIP-01 v1"
    assert second.proposal.approved_by == APPROVER
    assert APPROVER in second.proposal.rationale
    assert "SHORT-SHIP-01 v1" in second.proposal.rationale
    assert second.proposal.action is DecisionAction.SHORT_PAY
    assert second.proposal.amount_payable == cases["E2"].supported_amount

    # The counters tell the same story, counted from the store.
    counters = metrics.compute()
    assert counters.human_touches == 1
    # E1 and E2 are worked; E3, E4 and E5 are still open, and the counters say so.
    assert counters.worked == 2
    assert counters.open_not_worked == 3
    assert counters.worked + counters.open_not_worked == counters.exceptions_found
    assert counters.auto_cleared == 1
    assert counters.touches_avoided_by_policy == 1
    assert counters.policy_citations == 1
    assert policy.citations("SHORT-SHIP-01") == ["E2"]


def test_a_rule_does_not_reach_across_classes_or_suppliers(sources, cases) -> None:
    chromium_or_skip()
    investigate_engine.work(cases["E1"], sources)
    investigate_engine.apply_human_decision(cases["E1"], action=DecisionAction.APPROVE, by=APPROVER)
    learned = store.list_policies(active_only=True)[0]

    # A different class of exception, from a different supplier: no rule applies.
    price = investigate_engine.work(cases["E3"], sources)
    assert policy.match(cases["E3"], price) is None
    assert price.proposal is not None
    assert price.proposal.auto is False
    assert policy.covers(learned, cases["E3"], price) is False


def test_a_contradicting_decision_versions_the_rule_and_keeps_the_old_one(sources, cases) -> None:
    chromium_or_skip()
    investigate_engine.work(cases["E1"], sources)
    investigate_engine.apply_human_decision(cases["E1"], action=DecisionAction.APPROVE, by=APPROVER)
    second = investigate_engine.work(cases["E2"], sources)
    assert second.proposal is not None and second.proposal.auto is True

    # Somebody senior looks at the auto-cleared one and disagrees.
    _, narrowed = investigate_engine.apply_human_decision(
        cases["E2"],
        action=DecisionAction.REJECT,
        by="Dana, CFO",
        note="we are not short-paying this supplier again this quarter",
    )
    assert narrowed is not None
    assert narrowed.id == "SHORT-SHIP-01"
    assert narrowed.version == 2
    assert narrowed.supersedes_version == 1
    assert narrowed.approved_by == "Dana, CFO"
    # A rejection only ever narrows: the CFO's own unlimited authority does not raise what
    # the rule may clear by itself, which stays at the Controller's 10,000.
    assert narrowed.authority_ceiling == 10_000.00

    versions = {rule.version: rule for rule in store.list_policies()}
    assert set(versions) == {1, 2}
    assert versions[1].active is False, "v1 is kept for anything decided while it applied"
    assert versions[1].superseded_at is not None
    assert versions[2].active is True

    # And the narrower rule no longer covers the exception that was rejected.
    assert narrowed.condition.max_short_pct < cases["E2"].short_pct
    assert policy.match(cases["E2"], second) is None
