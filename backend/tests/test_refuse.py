"""Refusing is a feature. The fourth beat, and the reason the other three can be trusted.

Two things are proved here: an exception with nothing behind it is handed back with a list of
where Tieout looked, and a thin evidence pack is never rescued by a learned rule.
"""

from __future__ import annotations

from conftest import chromium_or_skip
from tieout.engine import decide, policy, store
from tieout.engine import investigate as investigate_engine
from tieout.engine.investigate import Sources
from tieout.engine.models import DecisionAction, ExceptionStatus, Source
from tieout.engine.sources.erp import ErpClient
from tieout.engine.sources.inbox import InboxClient

APPROVER = "Chris, Controller"
# E5 is 12,750 — above a Controller's limit — so the person who signs it off by hand has
# to be the CFO. That is the other half of test_authority.py, seen from here.
SENIOR = "Dana, CFO"


def test_the_unresolvable_invoice_is_refused_not_guessed(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.work(cases["E5"], sources)

    assert pack.proposal is not None
    proposal = pack.proposal
    assert proposal.action is DecisionAction.REFUSE
    assert proposal.confidence < decide.CONFIDENCE_FLOOR
    assert proposal.amount_payable is None, "a refusal never proposes paying anything"
    assert store.get_exception("E5").status is ExceptionStatus.REFUSED


def test_the_refusal_says_where_it_looked(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.work(cases["E5"], sources)
    rationale = pack.proposal.rationale

    assert "Here is where I looked" in rationale
    assert "You decide." in rationale
    for source in (Source.ERP, Source.INBOX, Source.PORTAL):
        assert any(step.source is source for step in pack.steps)
    assert all(not check.passed for check in pack.proposal.checks)


def test_a_refusal_is_not_an_error_and_teaches_nothing(sources, cases) -> None:
    chromium_or_skip()
    investigate_engine.work(cases["E5"], sources)

    # A person can still decide it by hand, but there is no pattern to generalise.
    decision, learned = investigate_engine.apply_human_decision(
        cases["E5"], action=DecisionAction.APPROVE, by=SENIOR, note="one-off, chased by phone"
    )
    assert decision.approved_by == SENIOR
    assert decision.action is DecisionAction.APPROVE
    assert learned is None
    assert store.list_policies() == []


def test_weak_evidence_never_auto_clears(world_urls, sources, cases) -> None:
    """The rule is not a shortcut: without the supplier's document, nothing clears itself."""
    chromium_or_skip()
    investigate_engine.work(cases["E1"], sources)
    investigate_engine.apply_human_decision(cases["E1"], action=DecisionAction.APPROVE, by=APPROVER)
    assert store.list_policies(active_only=True)

    with ErpClient(world_urls["erp"]) as erp, InboxClient(world_urls["inbox"]) as inbox:
        blind = Sources(erp=erp, inbox=inbox, use_portal=False)
        thin = investigate_engine.work(cases["E2"], blind)

    assert policy.match(cases["E2"], thin) is None
    assert thin.proposal is not None
    assert thin.proposal.auto is False
    assert thin.proposal.action is DecisionAction.REFUSE
    assert store.get_exception("E2").status is ExceptionStatus.REFUSED
