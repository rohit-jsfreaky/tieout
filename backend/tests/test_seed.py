"""Phase 1's finish line, as tests.

Forty invoices. Thirty-five tie out. Five are broken, each in the way the seed table says.
All three services answer, the portal really does keep you out until you sign in, and reset
puts everything back.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from tieout.world import seed
from tieout.world.erp import app as erp_app
from tieout.world.inbox import app as inbox_app
from tieout.world.portal import app as portal_app


@pytest.fixture
def erp() -> TestClient:
    return TestClient(erp_app)


@pytest.fixture
def inbox() -> TestClient:
    return TestClient(inbox_app)


@pytest.fixture
def portal() -> TestClient:
    return TestClient(portal_app, follow_redirects=False)


def _ties_out(invoice: seed.Invoice) -> bool:
    """The three-way match, written out here so the test does not depend on the engine."""
    if invoice.po_number is None:
        return False
    po = seed.get_purchase_order(invoice.po_number)
    receipts = seed.list_goods_receipts(po=invoice.po_number)
    if po is None or not receipts:
        return False
    ordered = {line.sku: line for line in po.lines}
    received = {line.sku: line.qty_received for receipt in receipts for line in receipt.lines}
    for line in invoice.lines:
        po_line = ordered.get(line.sku)
        if po_line is None:
            return False
        if line.qty != po_line.qty_ordered or line.qty != received.get(line.sku):
            return False
        if line.unit_price != po_line.unit_price:
            return False
    return True


# --------------------------------------------------------------------------------------
# The ledger
# --------------------------------------------------------------------------------------


def test_the_month_has_forty_invoices() -> None:
    assert len(seed.list_invoices()) == 40


def test_thirty_five_invoices_tie_out_and_five_do_not() -> None:
    invoices = seed.list_invoices()
    broken = [invoice.id for invoice in invoices if not _ties_out(invoice)]
    assert len(invoices) - len(broken) == 35
    assert sorted(broken) == sorted(row["invoice"] for row in seed.SEED_EXCEPTIONS)


def test_every_seeded_exception_is_broken_the_way_the_table_says() -> None:
    for row in seed.SEED_EXCEPTIONS:
        invoice = seed.get_invoice(row["invoice"])
        assert invoice is not None, row["invoice"]
        assert invoice.vendor_id == row["vendor"]

        if row["expected_class"] == "short_ship":
            po = seed.get_purchase_order(row["po"])
            receipt = seed.list_goods_receipts(po=row["po"])[0]
            assert po is not None
            assert invoice.lines[0].qty == po.lines[0].qty_ordered
            assert receipt.lines[0].qty_received < invoice.lines[0].qty
            assert invoice.lines[0].unit_price == po.lines[0].unit_price
        elif row["expected_class"] == "price_variance":
            po = seed.get_purchase_order(row["po"])
            receipt = seed.list_goods_receipts(po=row["po"])[0]
            assert po is not None
            assert receipt.lines[0].qty_received == invoice.lines[0].qty
            assert invoice.lines[0].unit_price > po.lines[0].unit_price
        elif row["expected_class"] == "missing_po":
            assert invoice.po_number is None
        elif row["expected_class"] == "unknown":
            assert invoice.po_number is None
            assert seed.list_goods_receipts(vendor=invoice.vendor_id) == []
        else:  # pragma: no cover - the seed table is closed
            raise AssertionError(f"unknown class {row['expected_class']}")


def test_price_variance_is_four_percent() -> None:
    invoice = seed.get_invoice("INV-3038")
    po = seed.get_purchase_order("PO-1044")
    assert invoice is not None and po is not None
    variance = invoice.lines[0].unit_price / po.lines[0].unit_price - 1
    assert round(variance * 100, 2) == 4.0


def test_the_missing_po_invoice_has_exactly_one_open_po_that_fits() -> None:
    invoice = seed.get_invoice("INV-3039")
    assert invoice is not None
    candidates = [
        po
        for po in seed.list_purchase_orders(vendor=invoice.vendor_id, status="open")
        if po.total == invoice.total
        and abs((po.order_date - invoice.invoice_date).days) <= 7
        and not seed.list_invoices(po=po.id)
    ]
    assert [po.id for po in candidates] == ["PO-1045"]


def test_the_unresolvable_invoice_has_nothing_anywhere() -> None:
    invoice = seed.get_invoice("INV-3040")
    assert invoice is not None
    vendor = seed.get_vendor(invoice.vendor_id)
    assert vendor is not None and vendor.on_supplier_network is False
    assert invoice.po_number is None
    assert seed.list_purchase_orders(vendor=invoice.vendor_id) == []
    assert seed.list_goods_receipts(vendor=invoice.vendor_id) == []
    assert seed.list_threads(vendor=invoice.vendor_id) == []
    assert seed.list_delivery_notes(vendor=invoice.vendor_id) == []


def test_dates_stay_inside_the_period() -> None:
    start = seed.period_start()
    for invoice in seed.list_invoices():
        assert start <= invoice.invoice_date < start.replace(day=28)


def test_the_seed_is_deterministic() -> None:
    first = seed.build_world(date(2026, 9, 15))
    second = seed.build_world(date(2026, 9, 15))
    assert first.model_dump_json() == second.model_dump_json()


# --------------------------------------------------------------------------------------
# The ERP, on :8701
# --------------------------------------------------------------------------------------


def test_erp_lists_forty_invoices(erp: TestClient) -> None:
    body = erp.get("/invoices").json()
    assert body["count"] == 40
    assert len(body["items"]) == 40


def test_erp_filters(erp: TestClient) -> None:
    assert erp.get("/invoices", params={"po": "PO-1042"}).json()["count"] == 1
    assert erp.get("/invoices", params={"vendor": "V-101"}).json()["count"] == 7
    assert erp.get("/purchase_orders", params={"status": "open"}).json()["count"] == 4
    assert erp.get("/goods_receipts", params={"po": "PO-1042"}).json()["count"] == 1
    assert erp.get("/vendors").json()["count"] == 8


def test_erp_gets_one_document_and_404s_the_rest(erp: TestClient) -> None:
    invoice = erp.get("/invoices/INV-3036").json()
    assert invoice["po_number"] == "PO-1042"
    assert invoice["lines"][0]["qty"] == 100
    assert erp.get("/invoices/INV-9999").status_code == 404


# --------------------------------------------------------------------------------------
# The portal, on :8702 — the source with no API
# --------------------------------------------------------------------------------------


def test_portal_keeps_you_out_until_you_sign_in(portal: TestClient) -> None:
    response = portal.get("/orders/PO-1042/delivery-note")
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/orders/PO-1042/delivery-note"


def test_portal_rejects_the_wrong_password(portal: TestClient) -> None:
    user, _ = seed.portal_credentials()
    response = portal.post("/login", data={"username": user, "password": "not-it"})
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login?")
    assert portal.cookies.get("vendorlink_session") is None


def test_portal_delivery_note_shows_the_short_shipment(portal: TestClient) -> None:
    user, password = seed.portal_credentials()
    signed_in = portal.post(
        "/login",
        data={"username": user, "password": password, "next": "/orders"},
    )
    assert signed_in.status_code == 303
    assert signed_in.headers["location"] == "/orders"
    assert portal.cookies.get("vendorlink_session")

    note = portal.get("/orders/PO-1042/delivery-note")
    assert note.status_code == 200
    assert "<strong>95</strong>" in note.text
    assert "Short shipment" in note.text
    assert "DN-1042" in note.text

    assert "PO-1042" in portal.get("/orders").text
    assert portal.post("/logout").status_code == 303
    assert portal.get("/orders").status_code == 303


# --------------------------------------------------------------------------------------
# The inbox, on :8703
# --------------------------------------------------------------------------------------


def test_inbox_finds_the_short_ship_thread(inbox: TestClient) -> None:
    body = inbox.get("/threads", params={"po": "PO-1042"}).json()
    assert body["count"] == 1
    thread = body["items"][0]
    assert thread["invoice_number"] == "INV-3036"
    assert "95 of the 100 boxes" in thread["messages"][0]["body"]


def test_inbox_search_and_filters(inbox: TestClient) -> None:
    assert inbox.get("/threads", params={"vendor": "V-101"}).json()["count"] == 2
    assert inbox.get("/threads", params={"invoice": "INV-3038"}).json()["count"] == 1
    assert inbox.get("/threads", params={"q": "surcharge"}).json()["count"] == 1
    assert inbox.get("/threads").json()["count"] == 7


def test_inbox_has_nothing_at_all_for_the_unresolvable_invoice(inbox: TestClient) -> None:
    assert inbox.get("/threads", params={"vendor": "V-108"}).json()["count"] == 0
    assert inbox.get("/threads", params={"invoice": "INV-3040"}).json()["count"] == 0


# --------------------------------------------------------------------------------------
# Reset
# --------------------------------------------------------------------------------------


def test_reset_puts_the_world_back(erp: TestClient) -> None:
    conn = seed.connect()
    try:
        with conn:
            conn.execute("DELETE FROM invoices WHERE id = 'INV-3036'")
    finally:
        conn.close()
    assert erp.get("/invoices").json()["count"] == 39

    seed.reset_world()

    assert erp.get("/invoices").json()["count"] == 40
    assert erp.get("/invoices/INV-3036").status_code == 200
    assert seed.summary()["counts"]["seeded_exceptions"] == 5
