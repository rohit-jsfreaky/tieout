"""The three-way match. Purchase order vs goods receipt vs invoice, for every open invoice.

This is the front door of the whole product: it is what lets Tieout ignore the invoices that
are fine and pick up only the ones that broke. It reads the ERP's API and nothing else — it
never sees the seed, so the five exceptions it finds are found the same way it would find
them in a real ledger.

An invoice ties out when, for every line, the quantity billed equals the quantity received
and the unit price equals the price on the order. Anything else is an exception, and it is
classed by what is actually wrong:

    short_ship       billed more than the warehouse received
    price_variance   quantities agree, the unit price does not
    missing_po       no order number on the invoice, but exactly one open order fits
    unknown          nothing lines up, or nothing to match against at all
"""

from __future__ import annotations

from datetime import date, datetime

import httpx

from .events import Event, EventKind, EventSink, null_sink
from .models import ExceptionCase, ExceptionKind, LineDiscrepancy
from .sources.erp import ErpClient, ErpInvoice, ErpPurchaseOrder

# A cent of rounding is not a price variance, and nothing under a whole unit is a short ship.
PRICE_TOLERANCE = 0.005
QTY_TOLERANCE = 0

# Matching an invoice with no PO number to an open order: same supplier, same money, same week.
CANDIDATE_AMOUNT_TOLERANCE = 0.01
CANDIDATE_WINDOW_DAYS = 14


def run(
    erp: ErpClient, *, sink: EventSink = null_sink, now: datetime | None = None
) -> list[ExceptionCase]:
    """Match every open invoice. Returns only the ones that did not tie out, in invoice order."""
    detected_at = now or datetime.now()
    vendors = {vendor.id: vendor.name for vendor in erp.vendors()}
    invoices = sorted(erp.invoices(status="open"), key=lambda inv: inv.id)
    orders = {po.id: po for po in erp.purchase_orders()}
    receipts_by_po: dict[str, dict[str, int]] = {}
    for receipt in erp.goods_receipts():
        booked = receipts_by_po.setdefault(receipt.po_id, {})
        for line in receipt.lines:
            booked[line.sku] = booked.get(line.sku, 0) + line.qty_received

    cases: list[ExceptionCase] = []
    for invoice in invoices:
        case = _classify(invoice, vendors, orders, receipts_by_po, detected_at)
        if case is None:
            continue
        case = case.model_copy(update={"id": f"E{len(cases) + 1}"})
        cases.append(case)

    sink(
        Event(
            kind=EventKind.MATCHED,
            message=(
                f"Three-way matched {len(invoices)} open invoices: "
                f"{len(invoices) - len(cases)} tie out, {len(cases)} do not."
            ),
        )
    )
    return cases


def _classify(
    invoice: ErpInvoice,
    vendors: dict[str, str],
    orders: dict[str, ErpPurchaseOrder],
    receipts_by_po: dict[str, dict[str, int]],
    detected_at: datetime,
) -> ExceptionCase | None:
    """One invoice against the ledger. ``None`` means it tied out and Tieout ignores it."""
    vendor_name = vendors.get(invoice.vendor_id, invoice.vendor_id)

    if invoice.po_number is None:
        return _classify_without_po(invoice, vendor_name, orders, receipts_by_po, detected_at)

    order = orders.get(invoice.po_number)
    if order is None:
        return _case(
            invoice,
            vendor_name,
            None,
            ExceptionKind.UNKNOWN,
            f"Invoice names order {invoice.po_number}, which is not in the ERP.",
            _lines_without_order(invoice),
            detected_at,
        )

    booked = receipts_by_po.get(order.id)
    if not booked:
        return _case(
            invoice,
            vendor_name,
            order.id,
            ExceptionKind.UNKNOWN,
            f"No goods receipt has ever been booked against {order.id}.",
            _lines_against_order(invoice, order, {}),
            detected_at,
        )

    lines = _lines_against_order(invoice, order, booked)
    short = sum(line.qty_short for line in lines)
    over_delivered = any(
        line.qty_received is not None and line.qty_received > line.qty_billed for line in lines
    )
    worst_price_delta = max((abs(line.price_delta) for line in lines), default=0.0)

    if short > QTY_TOLERANCE:
        billed = sum(line.qty_billed for line in lines)
        received = sum(line.qty_received or 0 for line in lines)
        return _case(
            invoice,
            vendor_name,
            order.id,
            ExceptionKind.SHORT_SHIP,
            f"Invoice bills {billed} units against {order.id}; the warehouse received {received}.",
            lines,
            detected_at,
        )
    if over_delivered:
        return _case(
            invoice,
            vendor_name,
            order.id,
            ExceptionKind.UNKNOWN,
            f"More was received against {order.id} than the invoice bills for.",
            lines,
            detected_at,
        )
    if worst_price_delta > PRICE_TOLERANCE:
        worst = max(lines, key=lambda line: abs(line.price_delta))
        return _case(
            invoice,
            vendor_name,
            order.id,
            ExceptionKind.PRICE_VARIANCE,
            (
                f"Invoiced at {worst.unit_price_billed:,.2f} per unit against "
                f"{worst.unit_price_ordered:,.2f} on {order.id} "
                f"({worst.price_delta_pct:+.2f}%)."
            ),
            lines,
            detected_at,
        )
    return None


def _classify_without_po(
    invoice: ErpInvoice,
    vendor_name: str,
    orders: dict[str, ErpPurchaseOrder],
    receipts_by_po: dict[str, dict[str, int]],
    detected_at: datetime,
) -> ExceptionCase:
    """No PO number on the invoice. Exactly one open order that fits is a missing PO."""
    candidates = [
        order
        for order in orders.values()
        if order.vendor_id == invoice.vendor_id
        and order.status == "open"
        and abs(order.total - invoice.total) <= CANDIDATE_AMOUNT_TOLERANCE
        and abs((order.order_date - invoice.invoice_date).days) <= CANDIDATE_WINDOW_DAYS
    ]
    if len(candidates) == 1:
        candidate = candidates[0]
        booked = receipts_by_po.get(candidate.id, {})
        return _case(
            invoice,
            vendor_name,
            candidate.id,
            ExceptionKind.MISSING_PO,
            (
                f"No order number on the invoice. {candidate.id} is the only open order for "
                f"{vendor_name} at {candidate.total:,.2f} in the same week."
            ),
            _lines_against_order(invoice, candidate, booked),
            detected_at,
        )
    if candidates:
        headline = (
            f"No order number on the invoice, and {len(candidates)} open orders for "
            f"{vendor_name} could fit it."
        )
    else:
        headline = (
            f"No order number, no matching open order and no goods receipt for {vendor_name}."
        )
    return _case(
        invoice,
        vendor_name,
        None,
        ExceptionKind.UNKNOWN,
        headline,
        _lines_without_order(invoice),
        detected_at,
    )


def _lines_against_order(
    invoice: ErpInvoice, order: ErpPurchaseOrder, booked: dict[str, int]
) -> list[LineDiscrepancy]:
    ordered = {line.sku: line for line in order.lines}
    lines: list[LineDiscrepancy] = []
    for line in invoice.lines:
        order_line = ordered.get(line.sku)
        lines.append(
            LineDiscrepancy(
                line_no=line.line_no,
                sku=line.sku,
                description=line.description,
                qty_billed=line.qty,
                qty_received=booked.get(line.sku) if booked else None,
                qty_ordered=order_line.qty_ordered if order_line else None,
                unit_price_billed=line.unit_price,
                unit_price_ordered=order_line.unit_price if order_line else None,
            )
        )
    return lines


def _lines_without_order(invoice: ErpInvoice) -> list[LineDiscrepancy]:
    return [
        LineDiscrepancy(
            line_no=line.line_no,
            sku=line.sku,
            description=line.description,
            qty_billed=line.qty,
            unit_price_billed=line.unit_price,
        )
        for line in invoice.lines
    ]


def _case(
    invoice: ErpInvoice,
    vendor_name: str,
    po_id: str | None,
    kind: ExceptionKind,
    headline: str,
    lines: list[LineDiscrepancy],
    detected_at: datetime,
) -> ExceptionCase:
    return ExceptionCase(
        id=invoice.id,  # replaced with E1..En once the whole ledger has been matched
        invoice_id=invoice.id,
        vendor_id=invoice.vendor_id,
        vendor_name=vendor_name,
        po_id=po_id,
        kind=kind,
        headline=headline,
        amount=invoice.total,
        currency=invoice.currency,
        invoice_date=invoice.invoice_date,
        detected_at=detected_at,
        lines=lines,
    )


def erp_is_up(base_url: str, timeout: float = 2.0) -> bool:
    """Cheap liveness check, so the CLI can tell a human the world is not running."""
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/health", timeout=timeout)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def period_of(when: date) -> str:
    return f"{when:%B %Y}"
