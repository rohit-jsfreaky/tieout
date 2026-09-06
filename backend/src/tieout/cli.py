"""The ``tieout`` command. The engine emits events; this file is the only thing that prints.

tieout world      run the fake company (ERP, vendor portal, AP mailbox)
tieout match      three-way match every open invoice, list what broke
tieout work E1    investigate one exception, then clear it or escalate it
tieout decide E1 approve --by "Chris, Controller"    (or --by Chris --role controller)
tieout policies   the rules Tieout has learned, every version
tieout metrics    human touches, auto-clears, evidence, citations
tieout demo       the four beats, end to end, from a fresh reset
tieout reset      the world and Tieout's own memory back to the seed
"""

from __future__ import annotations

import argparse
import shutil
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import httpx

from .engine import authority, load_env, match, metrics, policy, store
from .engine import investigate as investigate_engine
from .engine.events import Event, EventKind
from .engine.models import DecisionAction, EvidencePack, ExceptionCase, Metrics, Policy
from .engine.sources.erp import ErpClient
from .engine.sources.erp import default_base_url as erp_url
from .engine.sources.inbox import InboxClient
from .engine.sources.portal import default_base_url as portal_url
from .engine.sources.portal import forget_session, screenshot_dir
from .world import __main__ as world_main

WIDTH = 96
INDENT = "         "
DEMO_APPROVER = "Chris, Controller"


# --------------------------------------------------------------------------------------
# Printing
# --------------------------------------------------------------------------------------


def _wrap(text: str, indent: str = INDENT, first: str = "") -> str:
    return textwrap.fill(
        " ".join(text.split()),
        width=WIDTH,
        initial_indent=first or indent,
        subsequent_indent=indent,
    )


def _rule(title: str = "") -> None:
    print()
    print("=" * WIDTH)
    if title:
        print(f"  {title}")
        print("=" * WIDTH)


def _render(event: Event) -> None:
    """One event, one block of text. This is the whole terminal UI."""
    if event.kind is EventKind.MATCHED:
        print(_wrap(event.message, indent="  ", first="  "))
    elif event.kind is EventKind.INVESTIGATING:
        print()
        print(_wrap(event.message, indent="  ", first="  "))
    elif event.kind is EventKind.STEP and event.step is not None:
        step = event.step
        mark = f"[{step.source.value}]"
        tail = "" if step.found else "  ... nothing there"
        note = f"  ({step.note})" if step.note else ""
        print(_wrap(f"{step.action}{tail}{note}", indent=INDENT, first=f"  {mark:<9}"))
    elif event.kind is EventKind.FACT and event.fact is not None:
        fact = event.fact
        print(_wrap(fact.statement, indent=INDENT, first="  FACT     "))
        trail = f"{fact.source.value} · {fact.locator} · read by {fact.extracted_by}"
        if fact.screenshot:
            trail += f" · screenshot {fact.screenshot}"
        print(_wrap(trail, indent=INDENT + "  ", first=INDENT + "  "))
    elif event.kind is EventKind.ENOUGH:
        print(_wrap(event.message, indent=INDENT, first="  ENOUGH   "))
    elif event.kind is EventKind.WARNING:
        print(_wrap(event.message, indent=INDENT, first="  NOTE     "))
    elif event.kind is EventKind.AUTO_CLEARED:
        print()
        print(_wrap(event.message, indent="  ", first="  AUTO-CLEARED  "))
    elif event.kind is EventKind.POLICY_LEARNED:
        print()
        print(_wrap(event.message, indent="  ", first="  POLICY   "))
    elif event.kind is EventKind.POLICY_VERSIONED:
        print()
        print(_wrap(event.message, indent="  ", first="  POLICY   "))
    elif event.kind is EventKind.ESCALATED:
        print()
        print(_wrap(event.message, indent="  ", first="  ESCALATED  "))
    elif event.kind is EventKind.DECIDED:
        print()
        print(_wrap(event.message, indent="  ", first="  DECIDED  "))
    elif event.kind in {EventKind.PROPOSED, EventKind.REFUSED}:
        pass  # the pack is printed in full straight afterwards
    else:
        print(_wrap(event.message, indent="  ", first="  "))


def _print_decision(pack: EvidencePack) -> None:
    decision = pack.proposal
    if decision is None:
        return
    print()
    if decision.action is DecisionAction.REFUSE:
        headline = f"REFUSED — confidence {decision.confidence:.0%}"
    elif decision.action is DecisionAction.ESCALATE:
        headline = f"ESCALATED — needs the {decision.authority_needed}"
    elif decision.auto:
        headline = (
            f"AUTO-CLEARED — {decision.action.value}, citing {decision.cited_policy}, "
            f"approved by {decision.approved_by}"
        )
    else:
        headline = f"PROPOSED — {decision.action.value}, confidence {decision.confidence:.0%}"
    print(f"  {headline}")
    print(_wrap(decision.summary, indent="  ", first="  "))
    if decision.amount_for_authority is not None and decision.authority_needed is not None:
        print(
            _wrap(
                f"authorises {decision.amount_for_authority:,.2f} for payment — "
                f"{decision.authority_needed} authority "
                f"({authority.describe_limit(decision.authority_needed)})",
                indent="  ",
                first="  ",
            )
        )
    print()
    for line in decision.rationale.splitlines():
        print(_wrap(line, indent="    ", first="    ") if line.strip() else "")
    print()
    print("  Checklist")
    for check in decision.checks:
        mark = "ok" if check.passed else "NO"
        print(_wrap(f"{check.name} — {check.detail}", indent="            ", first=f"    {mark}  "))
    if decision.rationale_by not in {"code", "human"}:
        print(f"\n  (the paragraph above was drafted by {decision.rationale_by})")


def _print_queue(cases: list[ExceptionCase]) -> None:
    print()
    print(f"  {'ID':<4}{'INVOICE':<11}{'SUPPLIER':<30}{'CLASS':<16}{'AT STAKE':>11}  STATUS")
    print(f"  {'-' * (WIDTH - 4)}")
    for case in cases:
        supplier = case.vendor_name[:28]
        print(
            f"  {case.id:<4}{case.invoice_id:<11}{supplier:<30}{case.kind.value:<16}"
            f"{case.exposure:>11,.2f}  {case.status.value}"
        )
        print(_wrap(case.headline, indent="      ", first="      "))


def _print_policies(policies: list[Policy]) -> None:
    if not policies:
        print("\n  No rules yet. Tieout has not been shown a decision to learn from.")
        return
    for rule in policies:
        state = "active" if rule.active else f"superseded {rule.superseded_at:%Y-%m-%d}"
        cited = policy.citations(rule.id)
        print()
        print(f"  {rule.ref}  [{state}]  {rule.name}")
        print(_wrap(f"when: {rule.condition.describe()}", indent="        ", first="        "))
        print(f"        then: {rule.action.value}")
        print(
            _wrap(
                f"approved by {rule.approved_by} on {rule.approved_at:%d %B %Y}"
                f" · may clear up to {authority.describe_limit(rule.approved_role)}"
                f" · learned from {rule.learned_from} ({rule.learned_from_invoice})"
                f" · drafted by {rule.drafted_by}",
                indent="        ",
                first="        ",
            )
        )
        print(_wrap(rule.rationale, indent="        ", first="        "))
        if cited:
            print(f"        cited by: {', '.join(sorted(set(cited)))}")


def _print_metrics(counters: Metrics) -> None:
    rows = [
        ("Exceptions found", counters.exceptions_found),
        ("Worked", counters.worked),
        ("Open, not yet worked", counters.open_not_worked),
        ("Human touches", counters.human_touches),
        ("Auto-cleared by a learned rule", counters.auto_cleared),
        ("Human touches avoided", counters.touches_avoided_by_policy),
        ("Refused (handed back)", counters.refused),
        ("Waiting on a person", counters.awaiting_human),
        ("Evidence items on the trail", counters.evidence_items),
        ("Screenshots", counters.screenshots),
        ("Active policies", counters.policies_active),
        ("Policy citations", counters.policy_citations),
    ]
    print()
    for label, value in rows:
        print(f"  {label:<34}{value:>6}")


# --------------------------------------------------------------------------------------
# Wiring
# --------------------------------------------------------------------------------------


def _world_is_up() -> bool:
    try:
        return httpx.get(f"{erp_url()}/health", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


@contextmanager
def _world(quiet: bool = False) -> Iterator[None]:
    """Use the running world if there is one; otherwise run it for as long as we need it."""
    if _world_is_up():
        yield
        return
    if not quiet:
        print("  (the world was not running — starting the ERP, the portal and the mailbox)")
    running = world_main.start_background()
    try:
        yield
    finally:
        running.stop()


@contextmanager
def _sources(use_portal: bool = True) -> Iterator[investigate_engine.Sources]:
    with ErpClient() as erp, InboxClient() as inbox:
        yield investigate_engine.Sources(
            erp=erp,
            inbox=inbox,
            portal_base_url=portal_url(),
            use_portal=use_portal,
        )


def _refresh_queue() -> list[ExceptionCase]:
    """Re-run the match and persist it. Cheap, deterministic, and never reads the seed."""
    with ErpClient() as erp:
        cases = match.run(erp, sink=_render)
    store.save_exceptions(cases)
    return store.list_exceptions()


def _find(exception_id: str) -> ExceptionCase | None:
    case = store.get_exception(exception_id)
    if case is not None:
        return case
    _refresh_queue()
    return store.get_exception(exception_id)


# --------------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------------


def cmd_match() -> int:
    with _world():
        cases = _refresh_queue()
    _print_queue(cases)
    print()
    print("  Everything else tied out and was never touched.")
    return 0


def cmd_work(exception_id: str, use_portal: bool = True) -> int:
    with _world():
        case = _find(exception_id)
        if case is None:
            print(f"  No exception called {exception_id}. Run `tieout match` first.")
            return 1
        with _sources(use_portal=use_portal) as sources:
            pack = investigate_engine.work(case, sources, sink=_render, today=date.today())
    _print_decision(pack)
    return 0


def cmd_decide(
    exception_id: str, action: str, by: str, note: str = "", role: str | None = None
) -> int:
    case = _find(exception_id)
    if case is None:
        print(f"  No exception called {exception_id}. Run `tieout match` first.")
        return 1
    try:
        decision, learned = investigate_engine.apply_human_decision(
            case,
            action=DecisionAction(action),
            by=by,
            role=role,
            note=note,
            sink=_render,
            today=date.today(),
        )
    except investigate_engine.NotInvestigated as exc:
        print(f"  {exc}")
        return 1
    except authority.UnknownRole as exc:
        print(f"  {exc}")
        return 1
    if decision.action is DecisionAction.ESCALATE:
        # Not a failure of the agent: the control fired. Nothing paid, nothing learned.
        print(_wrap(decision.rationale, indent="  ", first="  "))
        return 1
    if learned is not None:
        _print_policies([learned])
    elif decision.action is not DecisionAction.REFUSE:
        print("\n  No rule learned from this one.")
    return 0


def cmd_policies() -> int:
    _print_policies(store.list_policies())
    return 0


def cmd_metrics() -> int:
    _print_metrics(metrics.compute())
    return 0


def cmd_reset(quiet: bool = False) -> int:
    """The world back to the seed, and Tieout back to knowing nothing."""
    if quiet:
        world_main.seed.reset_world()
    else:
        world_main.reset()
    store.reset()
    forget_session()
    shots = screenshot_dir()
    if shots.exists():
        shutil.rmtree(shots, ignore_errors=True)
    print("  Tieout's memory is empty too: no packs, no decisions, no policies, no session.")
    return 0


def cmd_demo(use_portal: bool = True) -> int:
    """The four beats, in order, from a cold start. This is the demo the video records."""
    load_env()
    cmd_reset(quiet=True)

    with _world(quiet=True), _sources(use_portal=use_portal) as sources:
        _rule("THE QUEUE — 40 open invoices, three-way matched. Only the broken ones are picked up")
        cases = _refresh_queue()
        _print_queue(cases)

        by_id = {case.id: case for case in cases}
        first = _pick(cases, "short_ship", 0)
        second = _pick(cases, "short_ship", 1)
        hopeless = _pick(cases, "unknown", 0)
        if first is None or second is None or hopeless is None:
            print("\n  The world does not hold the two short-ships and the unresolvable one.")
            return 1

        _rule(f"BEAT 1 — Investigate: {first.id} across the ERP, the mailbox and the portal")
        pack = investigate_engine.work(by_id[first.id], sources, sink=_render)
        _print_decision(pack)

        _rule(f"BEAT 2 — Decide once: {DEMO_APPROVER} approves, and a rule is born")
        cmd_decide(first.id, "approve", DEMO_APPROVER)

        _rule(f"BEAT 3 — Clears itself: {second.id} never reaches a person")
        pack = investigate_engine.work(by_id[second.id], sources, sink=_render)
        _print_decision(pack)

        _rule(f"BEAT 4 — Refuses: nothing lines up on {hopeless.id}, so Tieout stops")
        pack = investigate_engine.work(by_id[hopeless.id], sources, sink=_render)
        _print_decision(pack)

    _rule("THE RULE TIEOUT LEARNED")
    _print_policies(store.list_policies())

    _rule("THE COUNTERS")
    _print_metrics(metrics.compute())
    print()
    print("  Every number above was counted from this run. Nothing here is typed in.")
    return 0


def _pick(cases: list[ExceptionCase], kind: str, index: int) -> ExceptionCase | None:
    matching = [case for case in cases if case.kind.value == kind]
    return matching[index] if len(matching) > index else None


# --------------------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tieout",
        description="An agent that only works the invoices that broke.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    world = commands.add_parser("world", help="run the fake company (ERP, portal, inbox)")
    world.add_argument("--fresh", action="store_true", help="reseed the world before serving")
    world.add_argument("--host", default=world_main.HOST, help="bind address")
    world.add_argument("--verbose", action="store_true", help="show uvicorn access logs")

    commands.add_parser("match", help="three-way match every open invoice")

    work = commands.add_parser("work", help="investigate one exception")
    work.add_argument("exception", help="E1, or the invoice number")
    work.add_argument(
        "--no-portal", action="store_true", help="skip the browser (evidence will be thinner)"
    )

    decide = commands.add_parser("decide", help="record a human decision and learn from it")
    decide.add_argument("exception", help="E1, or the invoice number")
    decide.add_argument(
        "action",
        choices=[
            DecisionAction.APPROVE.value,
            DecisionAction.REJECT.value,
            DecisionAction.SHORT_PAY.value,
            DecisionAction.ATTACH_PO.value,
        ],
        help="approve = do what Tieout proposed",
    )
    decide.add_argument("--by", required=True, help='who decided, e.g. "Chris, Controller"')
    decide.add_argument(
        "--role",
        default=None,
        help="their seat in the delegation-of-authority matrix: AP Clerk, Controller or CFO",
    )
    decide.add_argument("--note", default="", help="anything the approver wants on the record")

    commands.add_parser("policies", help="the rules Tieout has learned")
    commands.add_parser("metrics", help="human touches, auto-clears, evidence")

    demo = commands.add_parser("demo", help="the four beats, end to end")
    demo.add_argument("--no-portal", action="store_true", help="skip the browser")

    commands.add_parser("reset", help="the world and Tieout's memory back to the seed")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "world":
        if args.fresh:
            world_main.seed.reset_world()
        return world_main.serve(host=args.host, verbose=args.verbose)
    if args.command == "match":
        return cmd_match()
    if args.command == "work":
        return cmd_work(args.exception, use_portal=not args.no_portal)
    if args.command == "decide":
        return cmd_decide(args.exception, args.action, args.by, args.note, args.role)
    if args.command == "policies":
        return cmd_policies()
    if args.command == "metrics":
        return cmd_metrics()
    if args.command == "demo":
        return cmd_demo(use_portal=not args.no_portal)
    if args.command == "reset":
        return cmd_reset()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
