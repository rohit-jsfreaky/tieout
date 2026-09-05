"""The audit trail. Every fact has a source, a time and a way to check it — or it is refused.

The portal test drives a real Chromium against the real portal, because the claim being
tested is "Tieout signed in and read the document", and a mock cannot fail the way a login
can.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from conftest import chromium_or_skip
from tieout.engine import investigate as investigate_engine
from tieout.engine.evidence import EvidenceError, EvidenceTrail
from tieout.engine.models import FactKind, Figures, Source
from tieout.engine.sources import portal

PERIOD_START = date(2026, 9, 1)


def test_every_fact_carries_its_source_time_and_locator(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.investigate(cases["E1"], sources)

    assert pack.facts, "an investigation with no evidence is not an investigation"
    for fact in pack.facts:
        assert fact.source in set(Source)
        assert fact.observed_at is not None
        assert fact.locator.strip()
        assert fact.raw.strip()
        assert fact.statement.strip()
        assert fact.exception_id == "E1"


def test_the_portal_fact_has_a_screenshot_that_is_really_on_disk(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.investigate(cases["E1"], sources)

    notes = pack.facts_of(FactKind.DELIVERY_NOTE)
    assert notes, "a short ship must be backed by the supplier's own document"
    note = notes[0]
    assert note.source is Source.PORTAL
    assert note.screenshot and Path(note.screenshot).is_file()
    assert Path(note.screenshot).stat().st_size > 0
    assert note.figures.qty_shipped == 95


def test_all_three_sources_are_visited_and_dead_ends_are_recorded(sources, cases) -> None:
    chromium_or_skip()
    pack = investigate_engine.investigate(cases["E5"], sources)

    assert set(pack.sources_used) == {Source.ERP, Source.INBOX, Source.PORTAL}
    assert any(not step.found for step in pack.steps), "silence is evidence and must be logged"


def test_the_session_is_saved_on_the_first_sign_in_and_reused_afterwards(sources, cases) -> None:
    """Tier 2 of the production auth story: log in once, reuse the session."""
    chromium_or_skip()
    portal.forget_session()

    first = investigate_engine.investigate(cases["E1"], sources)
    assert any("signed in to VendorLink" in step.action for step in first.steps)
    assert portal.session_file().is_file()

    second = investigate_engine.investigate(cases["E2"], sources)
    assert any("reused the saved VendorLink session" in step.action for step in second.steps)
    assert not any("signed in to VendorLink" in step.action for step in second.steps)


# --------------------------------------------------------------------------------------
# What evidence.py refuses to write down
# --------------------------------------------------------------------------------------


def _trail(cases) -> EvidenceTrail:
    return EvidenceTrail(cases["E1"], period_start=PERIOD_START)


def test_a_portal_fact_without_a_screenshot_is_refused(cases) -> None:
    with pytest.raises(EvidenceError, match="screenshot"):
        _trail(cases).record(
            source=Source.PORTAL,
            kind=FactKind.DELIVERY_NOTE,
            statement="the portal said 95 were shipped",
            locator="http://127.0.0.1:8702/orders/PO-1042/delivery-note",
            raw="95 shipped",
        )


def test_a_screenshot_path_that_is_not_on_disk_is_refused(cases, tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="not on disk"):
        _trail(cases).record(
            source=Source.PORTAL,
            kind=FactKind.DELIVERY_NOTE,
            statement="the portal said 95 were shipped",
            locator="http://127.0.0.1:8702/orders/PO-1042/delivery-note",
            raw="95 shipped",
            screenshot=tmp_path / "never-taken.png",
        )


def test_a_fact_dated_in_the_wrong_year_is_refused(cases) -> None:
    """The model guessed 2024 on the first live call. That must never reach the trail."""
    with pytest.raises(EvidenceError, match="outside the open period"):
        _trail(cases).record(
            source=Source.INBOX,
            kind=FactKind.VENDOR_EMAIL,
            statement="the supplier said it shipped 95 units",
            locator="http://127.0.0.1:8703/threads/T-9001",
            raw="we shipped 95 of the 100 boxes on 8 September",
            figures=Figures(qty_shipped=95, event_date=date(2024, 9, 8)),
        )


def test_a_fact_with_nothing_behind_it_is_refused(cases) -> None:
    with pytest.raises(EvidenceError):
        _trail(cases).record(
            source=Source.ERP,
            kind=FactKind.INVOICE,
            statement="the invoice looks wrong",
            locator="",
            raw="{}",
        )
