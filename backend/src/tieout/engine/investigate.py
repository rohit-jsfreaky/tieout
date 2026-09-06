"""One exception, worked end to end: look, decide, and either clear it or hand it over.

The order is the order a person would use — the ledger first because it is cheap and
authoritative, then the mailbox, then the portal, because opening a browser is the slowest
and most expensive thing Tieout can do. After each source it asks ``decide.complete``: when
the class's checklist is already satisfied, it stops. A short-ship cannot be settled without
the supplier's own shipping document, so that one always ends up in the browser.

``work`` is the whole beat, shared by the CLI and (in Phase 3) the API, so neither of them
holds any logic of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from . import authority, decide, policy, store
from .events import Event, EventKind, EventSink, null_sink
from .evidence import EvidenceTrail
from .models import (
    Approver,
    Decision,
    DecisionAction,
    EvidencePack,
    ExceptionCase,
    ExceptionStatus,
    Policy,
    Role,
    Source,
)
from .sources import erp as erp_source
from .sources import inbox as inbox_source
from .sources import portal as portal_source


@dataclass
class Sources:
    """Where this run is allowed to look. Tests turn the browser off; the demo does not."""

    erp: erp_source.ErpClient
    inbox: inbox_source.InboxClient
    portal_base_url: str | None = None
    use_portal: bool = True


def investigate(
    case: ExceptionCase,
    sources: Sources,
    *,
    sink: EventSink = null_sink,
    today: date | None = None,
) -> EvidencePack:
    """Gather evidence until the class has what it needs, or until there is nowhere left."""
    today = today or date.today()
    period_start = sources.erp.period_start()
    trail = EvidenceTrail(case, period_start=period_start, sink=sink)

    sink(
        Event(
            kind=EventKind.INVESTIGATING,
            exception_id=case.id,
            message=(
                f"Investigating {case.id} — {case.invoice_id} from {case.vendor_name}: "
                f"{case.headline}"
            ),
        )
    )

    erp_source.collect(trail, case, sources.erp)
    if _enough(case, trail, sink, Source.ERP):
        return trail.pack()

    inbox_source.collect(trail, case, sources.inbox, today=today)
    if _enough(case, trail, sink, Source.INBOX):
        return trail.pack()

    if sources.use_portal:
        portal_source.collect(trail, case, base_url=sources.portal_base_url)

    return trail.pack()


def _enough(case: ExceptionCase, trail: EvidenceTrail, sink: EventSink, after: Source) -> bool:
    if not decide.complete(case, trail.facts):
        return False
    sink(
        Event(
            kind=EventKind.ENOUGH,
            exception_id=case.id,
            message=(
                f"Everything a {case.kind.value} needs is on the trail after the "
                f"{after.value}. Not opening the other sources."
            ),
        )
    )
    return True


def work(
    case: ExceptionCase,
    sources: Sources,
    *,
    sink: EventSink = null_sink,
    today: date | None = None,
) -> EvidencePack:
    """Investigate, then either clear it under a learned rule or propose and escalate."""
    pack = investigate(case, sources, sink=sink, today=today)

    rule = policy.match(case, pack)
    if rule is not None:
        decision = policy.apply(rule, case, pack)
        pack.proposal = decision
        store.save_pack(pack)
        store.save_decision(decision)
        store.set_status(case.id, ExceptionStatus.AUTO_CLEARED)
        sink(
            Event(
                kind=EventKind.AUTO_CLEARED,
                exception_id=case.id,
                message=(
                    f"Auto-cleared under {rule.ref}, approved by {rule.approved_by}. "
                    f"{decision.summary} No human needed."
                ),
                decision=decision,
                policy=rule,
            )
        )
        return pack

    proposal = decide.propose(pack, today=today)
    pack.proposal = proposal
    store.save_pack(pack)
    refused = proposal.action.value == "refuse"
    store.set_status(case.id, ExceptionStatus.REFUSED if refused else ExceptionStatus.PROPOSED)
    sink(
        Event(
            kind=EventKind.REFUSED if refused else EventKind.PROPOSED,
            exception_id=case.id,
            message=proposal.summary,
            decision=proposal,
        )
    )
    return pack


# --------------------------------------------------------------------------------------
# Beat two: the one human decision, and the rule that comes out of it
# --------------------------------------------------------------------------------------


class NotInvestigated(RuntimeError):
    """Nobody decides anything here without an evidence pack in front of them."""


def apply_human_decision(
    case: ExceptionCase,
    *,
    action: DecisionAction,
    by: str,
    role: str | Role | None = None,
    note: str = "",
    sink: EventSink = null_sink,
    today: date | None = None,
) -> tuple[Decision, Policy | None]:
    """Record what the human decided, then learn the rule that makes it the last time.

    Unless they are not allowed to decide it. An amount above the approver's own limit in the
    delegation-of-authority matrix is escalated rather than recorded: nothing is paid, nothing
    is learned, and the trail says who it needs instead.
    """
    pack = store.get_pack(case.id)
    if pack is None:
        raise NotInvestigated(f"{case.id} has not been investigated yet — run work first")

    approver = authority.approver_for(by, role)
    proposal = pack.proposal
    resolved = action
    if action is DecisionAction.APPROVE and proposal is not None:
        # "Approve" means "do what Tieout proposed", so the trail records the real action.
        if proposal.action not in {DecisionAction.REFUSE, DecisionAction.REJECT}:
            resolved = proposal.action

    signing = authority.amount_under_authority(case, resolved)
    if not authority.within_limit(approver.role, signing):
        return _escalate(case, pack, approver, signing, note, sink), None

    summary, payable, attach = decide.action_detail(case, resolved)
    checks = decide.checklist(case, pack.facts)
    decision = Decision(
        exception_id=case.id,
        action=resolved,
        summary=summary,
        rationale=(
            f"{approver.label} decided this by hand on {datetime.now():%d %B %Y}, authorising "
            f"{signing:,.2f} {case.currency} "
            f"{authority.against_limit(approver.role)}" + (f": {note}" if note else ".")
        ),
        rationale_by="human",
        confidence=decide.confidence(checks),
        checks=checks,
        auto=False,
        approved_by=approver.label,
        approved_role=approver.role,
        decided_at=datetime.now(),
        amount_payable=payable,
        attach_po=attach,
        amount_for_authority=signing,
        authority_needed=authority.role_needed_for(signing),
        note=note,
    )
    store.save_decision(decision)
    store.set_status(case.id, ExceptionStatus.RESOLVED)
    sink(
        Event(
            kind=EventKind.DECIDED,
            exception_id=case.id,
            message=f"{approver.label} chose {resolved.value}. {summary}",
            decision=decision,
        )
    )

    learned = policy.learn(pack, decision, approved_by=approver, today=today, sink=sink)
    return decision, learned


def _escalate(
    case: ExceptionCase,
    pack: EvidencePack,
    approver: Approver,
    signing: float,
    note: str,
    sink: EventSink,
) -> Decision:
    """Beat four's sibling: the agent knows what it found, and who is allowed to sign it.

    An escalation is an outcome, not an error. It goes on the trail with the name of the
    person who tried, so a month later it is clear the control fired rather than that
    somebody forgot.
    """
    needed = authority.role_needed_for(signing)
    sentence = authority.over_limit_sentence(approver.role, signing, case.currency)
    decision = Decision(
        exception_id=case.id,
        action=DecisionAction.ESCALATE,
        summary=sentence,
        rationale=(
            f"{approver.label} tried to settle {case.invoice_id} on {datetime.now():%d %B %Y}. "
            f"{sentence} Nothing has been paid and no rule was learned: a rule may never "
            f"clear more than the person who approved it could have cleared by hand. "
            f"Everything Tieout found is on the trail, waiting for a {needed.value}."
            + (f" Note from {approver.name}: {note}" if note else "")
        ),
        rationale_by="code",
        confidence=decide.confidence(decide.checklist(case, pack.facts)),
        checks=decide.checklist(case, pack.facts),
        auto=False,
        approved_by=approver.label,
        approved_role=approver.role,
        decided_at=datetime.now(),
        amount_for_authority=signing,
        authority_needed=needed,
        note=note,
    )
    store.save_decision(decision)
    store.set_status(case.id, ExceptionStatus.ESCALATED)
    sink(
        Event(
            kind=EventKind.ESCALATED,
            exception_id=case.id,
            message=f"Blocked: {sentence}",
            decision=decision,
        )
    )
    return decision
