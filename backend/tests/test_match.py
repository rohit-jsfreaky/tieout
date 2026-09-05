"""The three-way match finds the five broken invoices, and ignores the thirty-five good ones.

``SEED_EXCEPTIONS`` appears here, in a test, and nowhere in the engine. That is the point:
the test knows the answers, the engine has to work them out from the ERP like it would from
a real ledger.
"""

from __future__ import annotations

from pathlib import Path

from tieout.engine import match
from tieout.engine.models import ExceptionKind
from tieout.engine.sources.erp import ErpClient
from tieout.world import seed

ENGINE_DIR = Path(__file__).resolve().parents[1] / "src" / "tieout" / "engine"


def _matched(world_urls: dict[str, str]) -> list:
    with ErpClient(world_urls["erp"]) as erp:
        return match.run(erp)


def test_finds_exactly_the_five_seeded_exceptions(world_urls: dict[str, str]) -> None:
    found = _matched(world_urls)
    assert [case.invoice_id for case in found] == [
        entry["invoice"] for entry in seed.SEED_EXCEPTIONS
    ]
    assert [case.id for case in found] == ["E1", "E2", "E3", "E4", "E5"]


def test_every_exception_is_classed_the_way_the_seed_intended(
    world_urls: dict[str, str],
) -> None:
    by_invoice = {case.invoice_id: case for case in _matched(world_urls)}
    for entry in seed.SEED_EXCEPTIONS:
        case = by_invoice[entry["invoice"]]
        assert case.kind.value == entry["expected_class"], entry["ref"]


def test_the_thirty_five_clean_invoices_are_never_touched(world_urls: dict[str, str]) -> None:
    found = _matched(world_urls)
    broken = {case.invoice_id for case in found}
    all_invoices = {invoice.id for invoice in seed.list_invoices()}
    assert len(all_invoices) == 40
    assert len(all_invoices - broken) == 35


def test_the_numbers_behind_each_class(world_urls: dict[str, str]) -> None:
    by_id = {case.id: case for case in _matched(world_urls)}

    short = by_id["E1"]
    assert short.kind is ExceptionKind.SHORT_SHIP
    assert (short.qty_billed, short.qty_received, short.qty_short) == (100, 95, 5)
    assert short.short_pct == 5.0
    assert short.exposure == 92.50
    assert short.supported_amount == 1757.50

    smaller_short = by_id["E2"]
    assert smaller_short.short_pct == 3.33  # inside E1's learned tolerance, which is the point

    price = by_id["E3"]
    assert price.kind is ExceptionKind.PRICE_VARIANCE
    assert price.price_variance_pct == 4.0
    assert price.qty_short == 0

    missing = by_id["E4"]
    assert missing.kind is ExceptionKind.MISSING_PO
    assert missing.po_id == "PO-1045"  # found by matching supplier, amount and week

    hopeless = by_id["E5"]
    assert hopeless.kind is ExceptionKind.UNKNOWN
    assert hopeless.po_id is None


def test_the_engine_cannot_read_the_seed() -> None:
    """The architectural promise, enforced: no engine file imports the world or its answers."""
    offenders: list[str] = []
    for path in ENGINE_DIR.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "SEED_EXCEPTIONS" in source or "from ..world" in source or "tieout.world" in source:
            offenders.append(path.name)
    assert offenders == []
