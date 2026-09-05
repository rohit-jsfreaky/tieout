"""THE data of the fake company, and the SQLite it lives in.

Kestrel Manufacturing Co. buys from eight suppliers. Forty invoices are open this month.
Thirty-five of them tie out against their purchase order and their goods receipt. Five do
not, and every one of those five is broken on purpose (see ``SEED_EXCEPTIONS``).

The numbers are deterministic: same seed, same world, every run. Dates are anchored to the
first day of the current month so the world always looks like this month's work.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------------------
# The company, the currency, the portal account
# --------------------------------------------------------------------------------------

COMPANY_NAME = "Kestrel Manufacturing Co."
COMPANY_DOMAIN = "kestrelmfg.com"
CURRENCY = "USD"

PORTAL_NAME = "VendorLink"
PORTAL_TAGLINE = "Supplier network — orders, delivery notes and shipping documents"
DEFAULT_PORTAL_USER = f"ap-bot@{COMPANY_DOMAIN}"
DEFAULT_PORTAL_PASS = "tieout-demo"

PAYMENT_TERMS_DAYS = 30

# --------------------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------------------


class Vendor(BaseModel):
    id: str
    name: str
    contact_email: str
    payment_terms: str = f"Net {PAYMENT_TERMS_DAYS}"
    on_supplier_network: bool = True


class PurchaseOrderLine(BaseModel):
    line_no: int
    sku: str
    description: str
    qty_ordered: int
    unit_price: float


class PurchaseOrder(BaseModel):
    id: str
    vendor_id: str
    order_date: date
    currency: str = CURRENCY
    status: str  # open | closed
    lines: list[PurchaseOrderLine]
    total: float


class GoodsReceiptLine(BaseModel):
    line_no: int
    sku: str
    qty_received: int


class GoodsReceipt(BaseModel):
    id: str
    po_id: str
    vendor_id: str
    received_date: date
    lines: list[GoodsReceiptLine]


class InvoiceLine(BaseModel):
    line_no: int
    sku: str
    description: str
    qty: int
    unit_price: float
    amount: float


class Invoice(BaseModel):
    id: str
    vendor_id: str
    po_number: str | None
    invoice_date: date
    due_date: date
    currency: str = CURRENCY
    status: str = "open"
    lines: list[InvoiceLine]
    total: float


class EmailMessage(BaseModel):
    sender: str
    recipient: str
    sent_at: datetime
    body: str


class EmailThread(BaseModel):
    id: str
    subject: str
    vendor_id: str
    po_number: str | None = None
    invoice_number: str | None = None
    messages: list[EmailMessage]


class DeliveryNoteLine(BaseModel):
    line_no: int
    sku: str
    description: str
    qty_ordered: int
    qty_shipped: int


class DeliveryNote(BaseModel):
    id: str
    po_id: str
    vendor_id: str
    ship_date: date
    carrier: str
    tracking: str
    note: str = ""
    lines: list[DeliveryNoteLine]


class World(BaseModel):
    period_start: date
    vendors: list[Vendor] = Field(default_factory=list)
    purchase_orders: list[PurchaseOrder] = Field(default_factory=list)
    goods_receipts: list[GoodsReceipt] = Field(default_factory=list)
    invoices: list[Invoice] = Field(default_factory=list)
    email_threads: list[EmailThread] = Field(default_factory=list)
    delivery_notes: list[DeliveryNote] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# Money and dates
# --------------------------------------------------------------------------------------


def money(value: float | Decimal) -> float:
    """Round to whole cents, half up. Every amount in the world goes through here."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def period_start(today: date | None = None) -> date:
    """First day of the world's fiscal period.

    Defaults to the first of the current month. ``TIEOUT_SEED_MONTH=YYYY-MM`` pins it, which
    is what the tests use so a failure is reproducible in any month.
    """
    pinned = os.environ.get("TIEOUT_SEED_MONTH")
    if pinned:
        year, month = pinned.split("-")
        return date(int(year), int(month), 1)
    return (today or date.today()).replace(day=1)


def _day(start: date, n: int) -> date:
    """Day ``n`` of the period. Kept at 28 or below, so every month behaves the same."""
    return start + timedelta(days=n - 1)


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


# --------------------------------------------------------------------------------------
# The eight suppliers
# --------------------------------------------------------------------------------------

VENDORS: list[Vendor] = [
    Vendor(
        id="V-101",
        name="Northwind Industrial Supply",
        contact_email="orders@northwind-industrial.com",
    ),
    Vendor(id="V-102", name="Calder & Finch Paper Co.", contact_email="ar@calderfinch.com"),
    Vendor(id="V-103", name="Brightline Logistics", contact_email="billing@brightlinelog.com"),
    Vendor(id="V-104", name="Meridian Fasteners Ltd.", contact_email="sales@meridianfast.co"),
    Vendor(id="V-105", name="Halcyon Packaging Group", contact_email="accounts@halcyonpack.com"),
    Vendor(id="V-106", name="Stonebridge Electrical", contact_email="orders@stonebridge-elec.com"),
    Vendor(id="V-107", name="Verity Office Interiors", contact_email="hello@verityinteriors.com"),
    # E5's supplier. Not on the supplier network, so the portal has nothing on them either.
    Vendor(
        id="V-108",
        name="Ardent Systems LLC",
        contact_email="invoices@ardentsystems.io",
        payment_terms="Net 15",
        on_supplier_network=False,
    ),
]

CARRIERS = {
    "V-101": "Fenwick Freight",
    "V-102": "Rowan Parcel",
    "V-103": "Brightline (own fleet)",
    "V-104": "Fenwick Freight",
    "V-105": "Rowan Parcel",
    "V-106": "Sable Transport",
    "V-107": "Sable Transport",
}

# 35 clean order lines: (vendor_id, sku, description, qty, unit_price). Five per supplier.
CLEAN_CATALOGUE: list[tuple[str, str, str, int, float]] = [
    ("V-101", "NW-1050", "Hex bolt M10 x 40mm, zinc, box of 100", 40, 22.40),
    ("V-101", "NW-2210", "Stainless washer M12, box of 200", 25, 12.00),
    ("V-101", "NW-3300", "Nitrile gloves, size L, box of 100", 60, 9.75),
    ("V-101", "NW-4120", "Cable tie 300mm black, bag of 500", 30, 14.20),
    ("V-101", "NW-5075", "Threadlock compound, 50ml bottle", 18, 31.60),
    ("V-102", "CF-5501", "A4 copy paper 80gsm, box of 5 reams", 80, 50.00),
    ("V-102", "CF-5510", "A3 copy paper 80gsm, box of 5 reams", 20, 78.50),
    ("V-102", "CF-6120", "Thermal label roll 100 x 150mm", 45, 16.90),
    ("V-102", "CF-6400", "Kraft envelope C4, box of 250", 22, 27.30),
    ("V-102", "CF-7000", "Packing paper roll 600mm", 15, 42.10),
    ("V-103", "BL-FRT-01", "Outbound freight, week 1", 1, 3120.00),
    ("V-103", "BL-PAL-02", "Pallet handling, 40 pallets", 1, 640.00),
    ("V-103", "BL-EXP-03", "Expedited delivery surcharge", 1, 275.00),
    ("V-103", "BL-STO-04", "Warehouse storage, 30 days", 1, 1890.00),
    ("V-103", "BL-INB-05", "Inbound freight consolidation", 1, 2450.00),
    ("V-104", "MF-2001", "Socket cap screw M8 x 25mm, box of 200", 35, 19.80),
    ("V-104", "MF-2140", "Spring washer M8, box of 500", 28, 8.45),
    ("V-104", "MF-3310", "Rivet 4.8 x 12mm, box of 1000", 16, 33.20),
    ("V-104", "MF-4400", "Anchor bolt M16 x 120mm, box of 25", 12, 64.90),
    ("V-104", "MF-5520", "Nyloc nut M10, box of 250", 24, 15.60),
    ("V-105", "HP-1100", "Corrugated carton 400x300x300, bundle of 25", 50, 28.75),
    ("V-105", "HP-1200", "Stretch wrap 500mm x 300m", 36, 11.90),
    ("V-105", "HP-1300", "Void fill paper, bale", 14, 46.50),
    ("V-105", "HP-1400", "Strapping band 12mm, roll of 1000m", 20, 38.40),
    ("V-105", "HP-1500", "Pallet corner protector, pack of 100", 18, 22.15),
    ("V-106", "SE-0450", "Industrial LED batten 1500mm", 26, 74.30),
    ("V-106", "SE-0620", "Three-phase contactor 40A", 10, 128.75),
    ("V-106", "SE-0730", "Cable gland M20, pack of 50", 22, 17.60),
    ("V-106", "SE-0810", "Armoured cable 4mm 3-core, 100m drum", 8, 312.00),
    ("V-106", "SE-0940", "Emergency stop switch, IP66", 15, 58.20),
    ("V-107", "VO-3020", "Task chair, mesh back", 12, 245.00),
    ("V-107", "VO-3110", "Height-adjustable desk 1600mm", 8, 615.00),
    ("V-107", "VO-3200", "Acoustic panel 1200 x 600", 30, 89.50),
    ("V-107", "VO-3300", "Filing pedestal, three drawer", 14, 172.40),
    ("V-107", "VO-3410", "Monitor arm, dual", 18, 134.90),
]

# --------------------------------------------------------------------------------------
# The five deliberate exceptions
#
# FOR TESTS AND DOCUMENTATION ONLY. The engine never reads this table — it finds these five
# by running the three-way match, the same way it would on a real ledger.
# --------------------------------------------------------------------------------------

SEED_EXCEPTIONS: list[dict[str, str]] = [
    {
        "ref": "E1",
        "invoice": "INV-3036",
        "po": "PO-1042",
        "vendor": "V-101",
        "expected_class": "short_ship",
        "what_is_wrong": "invoice bills 100 boxes, goods receipt shows 95",
        "truth_lives": "portal delivery note (95 shipped) + vendor email",
        "intended_outcome": "short-pay for 95 — the human approves and the policy is born",
    },
    {
        "ref": "E2",
        "invoice": "INV-3037",
        "po": "PO-1043",
        "vendor": "V-101",
        "expected_class": "short_ship",
        "what_is_wrong": "invoice bills 60 boxes, goods receipt shows 58",
        "truth_lives": "portal delivery note (58 shipped) + vendor email",
        "intended_outcome": "auto-cleared by the policy learned from E1",
    },
    {
        "ref": "E3",
        "invoice": "INV-3038",
        "po": "PO-1044",
        "vendor": "V-102",
        "expected_class": "price_variance",
        "what_is_wrong": "invoiced at 52.00 per box against a PO price of 50.00 (4%)",
        "truth_lives": "vendor email announcing a 2.00 per box fuel surcharge",
        "intended_outcome": "approve inside tolerance",
    },
    {
        "ref": "E4",
        "invoice": "INV-3039",
        "po": "PO-1045",
        "vendor": "V-103",
        "expected_class": "missing_po",
        "what_is_wrong": "invoice carries no PO number",
        "truth_lives": "ERP: exactly one open PO for this vendor, same amount, same week",
        "intended_outcome": "attach the PO, approve",
    },
    {
        "ref": "E5",
        "invoice": "INV-3040",
        "po": "",
        "vendor": "V-108",
        "expected_class": "unknown",
        "what_is_wrong": "no PO, no goods receipt, no email, nothing on the supplier network",
        "truth_lives": "nowhere",
        "intended_outcome": "REFUSE — not confident, here is where I looked",
    },
]


# --------------------------------------------------------------------------------------
# Building the world
# --------------------------------------------------------------------------------------


def _po_total(lines: list[PurchaseOrderLine]) -> float:
    return money(
        sum(Decimal(str(line.qty_ordered)) * Decimal(str(line.unit_price)) for line in lines)
    )


def _invoice_line(
    line_no: int, sku: str, description: str, qty: int, unit_price: float
) -> InvoiceLine:
    return InvoiceLine(
        line_no=line_no,
        sku=sku,
        description=description,
        qty=qty,
        unit_price=unit_price,
        amount=money(Decimal(str(qty)) * Decimal(str(unit_price))),
    )


def _invoice_total(lines: list[InvoiceLine]) -> float:
    return money(sum(Decimal(str(line.amount)) for line in lines))


def _delivery_note(
    po: PurchaseOrder,
    ship_date: date,
    shipped: dict[str, int],
    note: str = "",
    tracking_seq: int = 0,
) -> DeliveryNote:
    """A delivery note mirrors the PO, except for the quantities actually shipped."""
    suffix = po.id.split("-")[-1]
    return DeliveryNote(
        id=f"DN-{suffix}",
        po_id=po.id,
        vendor_id=po.vendor_id,
        ship_date=ship_date,
        carrier=CARRIERS.get(po.vendor_id, "Fenwick Freight"),
        tracking=f"{po.vendor_id.replace('-', '')}{suffix}{tracking_seq:02d}",
        note=note,
        lines=[
            DeliveryNoteLine(
                line_no=line.line_no,
                sku=line.sku,
                description=line.description,
                qty_ordered=line.qty_ordered,
                qty_shipped=shipped.get(line.sku, line.qty_ordered),
            )
            for line in po.lines
        ],
    )


def _build_clean(world: World, start: date) -> None:
    """Thirty-five invoices that tie out: PO qty and price == receipt qty == invoice."""
    for index, (vendor_id, sku, description, qty, unit_price) in enumerate(CLEAN_CATALOGUE):
        order_day = _day(start, 1 + (index % 12))
        received_day = order_day + timedelta(days=4)
        invoice_day = order_day + timedelta(days=5)

        lines = [
            PurchaseOrderLine(
                line_no=1,
                sku=sku,
                description=description,
                qty_ordered=qty,
                unit_price=unit_price,
            )
        ]
        po = PurchaseOrder(
            id=f"PO-{1001 + index}",
            vendor_id=vendor_id,
            order_date=order_day,
            status="closed",
            lines=lines,
            total=_po_total(lines),
        )
        world.purchase_orders.append(po)

        world.goods_receipts.append(
            GoodsReceipt(
                id=f"GR-{2001 + index}",
                po_id=po.id,
                vendor_id=vendor_id,
                received_date=received_day,
                lines=[GoodsReceiptLine(line_no=1, sku=sku, qty_received=qty)],
            )
        )

        invoice_lines = [_invoice_line(1, sku, description, qty, unit_price)]
        world.invoices.append(
            Invoice(
                id=f"INV-{3001 + index}",
                vendor_id=vendor_id,
                po_number=po.id,
                invoice_date=invoice_day,
                due_date=invoice_day + timedelta(days=PAYMENT_TERMS_DAYS),
                lines=invoice_lines,
                total=_invoice_total(invoice_lines),
            )
        )

        world.delivery_notes.append(
            _delivery_note(po, received_day - timedelta(days=1), {}, tracking_seq=index)
        )


def _build_e1(world: World, start: date) -> None:
    """Short-ship: 100 boxes invoiced, 95 received. The portal note says 95."""
    sku, description, unit_price = "NW-8840", "Hex bolt M12 x 60mm, zinc, box of 50", 18.50
    ordered, received = 100, 95
    order_day = _day(start, 2)
    ship_day = _day(start, 8)
    received_day = _day(start, 9)
    invoice_day = _day(start, 10)

    lines = [
        PurchaseOrderLine(
            line_no=1,
            sku=sku,
            description=description,
            qty_ordered=ordered,
            unit_price=unit_price,
        )
    ]
    po = PurchaseOrder(
        id="PO-1042",
        vendor_id="V-101",
        order_date=order_day,
        status="open",
        lines=lines,
        total=_po_total(lines),
    )
    world.purchase_orders.append(po)
    world.goods_receipts.append(
        GoodsReceipt(
            id="GR-2042",
            po_id=po.id,
            vendor_id="V-101",
            received_date=received_day,
            lines=[GoodsReceiptLine(line_no=1, sku=sku, qty_received=received)],
        )
    )
    invoice_lines = [_invoice_line(1, sku, description, ordered, unit_price)]
    world.invoices.append(
        Invoice(
            id="INV-3036",
            vendor_id="V-101",
            po_number=po.id,
            invoice_date=invoice_day,
            due_date=invoice_day + timedelta(days=PAYMENT_TERMS_DAYS),
            lines=invoice_lines,
            total=_invoice_total(invoice_lines),
        )
    )
    world.delivery_notes.append(
        _delivery_note(
            po,
            ship_day,
            {sku: received},
            note=(
                f"Short shipment. {received} of {ordered} boxes despatched on "
                f"{ship_day.day} {ship_day:%B}. Balance of {ordered - received} boxes to follow "
                "next week from our Leeds warehouse."
            ),
            tracking_seq=42,
        )
    )
    world.email_threads.append(
        EmailThread(
            id="T-9001",
            subject=f"{po.id} — part shipment, {received} of {ordered} boxes",
            vendor_id="V-101",
            po_number=po.id,
            invoice_number="INV-3036",
            messages=[
                EmailMessage(
                    sender="dispatch@northwind-industrial.com",
                    recipient=f"ap@{COMPANY_DOMAIN}",
                    sent_at=_at(ship_day, 9, 12),
                    body=(
                        "Hello Kestrel AP team,\n\n"
                        f"A quick note on {po.id}. We shipped {received} of the {ordered} boxes of "
                        f"{sku} on {ship_day.day} {ship_day:%B}. The remaining "
                        f"{ordered - received} boxes are on back order and follow next week.\n\n"
                        "Our invoice was raised for the full order line before dispatch was "
                        "confirmed, so please short-pay to the delivered quantity if that is "
                        "easier at your end. The delivery note is on VendorLink.\n\n"
                        "Regards,\nPriya Raman\nDispatch, Northwind Industrial Supply"
                    ),
                )
            ],
        )
    )


def _build_e2(world: World, start: date) -> None:
    """The second short-ship, same supplier. This is the one the learned policy clears."""
    sku, description, unit_price = "NW-2210", "Stainless washer M12, box of 200", 12.00
    ordered, received = 60, 58
    order_day = _day(start, 5)
    ship_day = _day(start, 12)
    received_day = _day(start, 13)
    invoice_day = _day(start, 14)

    lines = [
        PurchaseOrderLine(
            line_no=1,
            sku=sku,
            description=description,
            qty_ordered=ordered,
            unit_price=unit_price,
        )
    ]
    po = PurchaseOrder(
        id="PO-1043",
        vendor_id="V-101",
        order_date=order_day,
        status="open",
        lines=lines,
        total=_po_total(lines),
    )
    world.purchase_orders.append(po)
    world.goods_receipts.append(
        GoodsReceipt(
            id="GR-2043",
            po_id=po.id,
            vendor_id="V-101",
            received_date=received_day,
            lines=[GoodsReceiptLine(line_no=1, sku=sku, qty_received=received)],
        )
    )
    invoice_lines = [_invoice_line(1, sku, description, ordered, unit_price)]
    world.invoices.append(
        Invoice(
            id="INV-3037",
            vendor_id="V-101",
            po_number=po.id,
            invoice_date=invoice_day,
            due_date=invoice_day + timedelta(days=PAYMENT_TERMS_DAYS),
            lines=invoice_lines,
            total=_invoice_total(invoice_lines),
        )
    )
    world.delivery_notes.append(
        _delivery_note(
            po,
            ship_day,
            {sku: received},
            note=(
                f"{received} of {ordered} boxes despatched on {ship_day.day} {ship_day:%B}. "
                f"{ordered - received} boxes were damaged on the pallet and withdrawn before "
                "loading; a credit note will follow."
            ),
            tracking_seq=43,
        )
    )
    world.email_threads.append(
        EmailThread(
            id="T-9002",
            subject=f"{po.id} — {ordered - received} boxes withdrawn, damaged",
            vendor_id="V-101",
            po_number=po.id,
            invoice_number="INV-3037",
            messages=[
                EmailMessage(
                    sender="dispatch@northwind-industrial.com",
                    recipient=f"ap@{COMPANY_DOMAIN}",
                    sent_at=_at(ship_day, 16, 40),
                    body=(
                        "Hi,\n\n"
                        f"Confirming {received} of {ordered} boxes of {sku} left us on "
                        f"{ship_day.day} {ship_day:%B} against {po.id}. Two boxes were damaged on "
                        "the pallet during loading and were withdrawn.\n\n"
                        "The invoice went out for the ordered quantity. Please pay the delivered "
                        "quantity; we will raise a credit for the difference.\n\n"
                        "Thanks,\nPriya Raman\nDispatch, Northwind Industrial Supply"
                    ),
                )
            ],
        )
    )


def _build_e3(world: World, start: date) -> None:
    """Price variance: 52.00 invoiced against a 50.00 PO price. Four percent."""
    sku = "CF-5501"
    description = "A4 copy paper 80gsm, box of 5 reams"
    po_price, invoiced_price, qty = 50.00, 52.00, 120
    order_day = _day(start, 3)
    ship_day = _day(start, 10)
    received_day = _day(start, 11)
    invoice_day = _day(start, 12)
    notice_day = _day(start, 1)

    lines = [
        PurchaseOrderLine(
            line_no=1, sku=sku, description=description, qty_ordered=qty, unit_price=po_price
        )
    ]
    po = PurchaseOrder(
        id="PO-1044",
        vendor_id="V-102",
        order_date=order_day,
        status="open",
        lines=lines,
        total=_po_total(lines),
    )
    world.purchase_orders.append(po)
    world.goods_receipts.append(
        GoodsReceipt(
            id="GR-2044",
            po_id=po.id,
            vendor_id="V-102",
            received_date=received_day,
            lines=[GoodsReceiptLine(line_no=1, sku=sku, qty_received=qty)],
        )
    )
    invoice_lines = [_invoice_line(1, sku, description, qty, invoiced_price)]
    world.invoices.append(
        Invoice(
            id="INV-3038",
            vendor_id="V-102",
            po_number=po.id,
            invoice_date=invoice_day,
            due_date=invoice_day + timedelta(days=PAYMENT_TERMS_DAYS),
            lines=invoice_lines,
            total=_invoice_total(invoice_lines),
        )
    )
    world.delivery_notes.append(
        _delivery_note(
            po,
            ship_day,
            {},
            note="Full quantity despatched. Fuel surcharge applies from this month, see notice.",
            tracking_seq=44,
        )
    )
    surcharge = money(Decimal(str(invoiced_price)) - Decimal(str(po_price)))
    world.email_threads.append(
        EmailThread(
            id="T-9003",
            subject="Fuel surcharge notice — effective this month",
            vendor_id="V-102",
            po_number=po.id,
            invoice_number="INV-3038",
            messages=[
                EmailMessage(
                    sender="ar@calderfinch.com",
                    recipient=f"ap@{COMPANY_DOMAIN}",
                    sent_at=_at(notice_day, 8, 5),
                    body=(
                        "Dear customer,\n\n"
                        f"From {notice_day.day} {notice_day:%B} a freight and fuel surcharge of "
                        f"{surcharge:.2f} {CURRENCY} per box applies to all {sku} deliveries. Our "
                        "haulage rates rose by 9% this quarter and we have absorbed the increase "
                        "for two quarters.\n\n"
                        f"Orders already placed at {po_price:.2f} will be invoiced at "
                        f"{invoiced_price:.2f} per box. No other line is affected.\n\n"
                        "Kind regards,\nAccounts Receivable, Calder & Finch Paper Co."
                    ),
                )
            ],
        )
    )


def _build_e4(world: World, start: date) -> None:
    """Missing PO: the invoice has no PO number. Exactly one open PO fits it."""
    sku, description, amount = "BL-FRT-02", "Outbound freight, week 2", 3480.00
    order_day = _day(start, 8)
    received_day = _day(start, 12)
    invoice_day = _day(start, 12)

    lines = [
        PurchaseOrderLine(
            line_no=1, sku=sku, description=description, qty_ordered=1, unit_price=amount
        )
    ]
    po = PurchaseOrder(
        id="PO-1045",
        vendor_id="V-103",
        order_date=order_day,
        status="open",
        lines=lines,
        total=_po_total(lines),
    )
    world.purchase_orders.append(po)
    world.goods_receipts.append(
        GoodsReceipt(
            id="GR-2045",
            po_id=po.id,
            vendor_id="V-103",
            received_date=received_day,
            lines=[GoodsReceiptLine(line_no=1, sku=sku, qty_received=1)],
        )
    )
    invoice_lines = [_invoice_line(1, sku, description, 1, amount)]
    world.invoices.append(
        Invoice(
            id="INV-3039",
            vendor_id="V-103",
            po_number=None,  # the whole point of E4
            invoice_date=invoice_day,
            due_date=invoice_day + timedelta(days=PAYMENT_TERMS_DAYS),
            lines=invoice_lines,
            total=_invoice_total(invoice_lines),
        )
    )
    world.delivery_notes.append(
        _delivery_note(po, received_day, {}, note="Weekly outbound consolidation.", tracking_seq=45)
    )
    world.email_threads.append(
        EmailThread(
            id="T-9004",
            subject="Weekly freight summary",
            vendor_id="V-103",
            po_number=None,  # deliberately does NOT name the PO
            invoice_number="INV-3039",
            messages=[
                EmailMessage(
                    sender="billing@brightlinelog.com",
                    recipient=f"ap@{COMPANY_DOMAIN}",
                    sent_at=_at(invoice_day, 11, 20),
                    body=(
                        "Hello,\n\n"
                        "Our invoice for last week's outbound consolidation is attached. Your "
                        "booking reference was raised by phone, so there is no order number on "
                        "our copy.\n\n"
                        "Brightline Logistics Billing"
                    ),
                )
            ],
        )
    )


def _build_e5(world: World, start: date) -> None:
    """Unresolvable: no PO, no receipt, no email, not on the supplier network."""
    description = "Professional services — systems integration, phase 1"
    amount = 12750.00
    invoice_day = _day(start, 13)
    invoice_lines = [_invoice_line(1, "SVC-INT-01", description, 1, amount)]
    world.invoices.append(
        Invoice(
            id="INV-3040",
            vendor_id="V-108",
            po_number=None,
            invoice_date=invoice_day,
            due_date=invoice_day + timedelta(days=15),
            lines=invoice_lines,
            total=_invoice_total(invoice_lines),
        )
    )


def _build_noise(world: World, start: date) -> None:
    """Ordinary correspondence, so searching the inbox is not a trick shot."""
    world.email_threads.extend(
        [
            EmailThread(
                id="T-9010",
                subject="Statement of account — this month",
                vendor_id="V-105",
                po_number="PO-1021",
                invoice_number="INV-3021",
                messages=[
                    EmailMessage(
                        sender="accounts@halcyonpack.com",
                        recipient=f"ap@{COMPANY_DOMAIN}",
                        sent_at=_at(_day(start, 6), 10, 0),
                        body=(
                            "Please find our statement of account for the current period. All "
                            "listed invoices are within terms. No action is needed if you have "
                            "already scheduled payment."
                        ),
                    )
                ],
            ),
            EmailThread(
                id="T-9011",
                subject="Delivery booked — PO-1026",
                vendor_id="V-106",
                po_number="PO-1026",
                invoice_number="INV-3026",
                messages=[
                    EmailMessage(
                        sender="orders@stonebridge-elec.com",
                        recipient=f"goods.in@{COMPANY_DOMAIN}",
                        sent_at=_at(_day(start, 7), 14, 30),
                        body=(
                            "Delivery is booked for Thursday morning between 08:00 and 12:00. "
                            "Full quantity on one pallet. The driver will call ahead."
                        ),
                    )
                ],
            ),
            EmailThread(
                id="T-9012",
                subject="Remittance query — INV-3031",
                vendor_id="V-107",
                po_number="PO-1031",
                invoice_number="INV-3031",
                messages=[
                    EmailMessage(
                        sender="hello@verityinteriors.com",
                        recipient=f"ap@{COMPANY_DOMAIN}",
                        sent_at=_at(_day(start, 9), 15, 45),
                        body=(
                            "Could you confirm the payment run date for INV-3031? The amount and "
                            "the order both look correct on our side, we are only chasing timing."
                        ),
                    )
                ],
            ),
        ]
    )


def build_world(today: date | None = None) -> World:
    """The whole fake company, in memory. Deterministic."""
    start = period_start(today)
    world = World(period_start=start, vendors=list(VENDORS))
    _build_clean(world, start)
    _build_e1(world, start)
    _build_e2(world, start)
    _build_e3(world, start)
    _build_e4(world, start)
    _build_e5(world, start)
    _build_noise(world, start)
    return world


# --------------------------------------------------------------------------------------
# Where the world is kept
# --------------------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE vendors (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE purchase_orders (
    id TEXT PRIMARY KEY, vendor_id TEXT NOT NULL, status TEXT NOT NULL,
    order_date TEXT NOT NULL, total REAL NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE goods_receipts (
    id TEXT PRIMARY KEY, po_id TEXT NOT NULL, vendor_id TEXT NOT NULL,
    received_date TEXT NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE invoices (
    id TEXT PRIMARY KEY, vendor_id TEXT NOT NULL, po_number TEXT, status TEXT NOT NULL,
    invoice_date TEXT NOT NULL, total REAL NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE email_threads (
    id TEXT PRIMARY KEY, vendor_id TEXT NOT NULL, po_number TEXT, invoice_number TEXT,
    subject TEXT NOT NULL, body TEXT NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE delivery_notes (
    id TEXT PRIMARY KEY, po_id TEXT NOT NULL, vendor_id TEXT NOT NULL,
    ship_date TEXT NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE world_meta (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
);
"""


def tieout_home() -> Path:
    return Path(os.environ.get("TIEOUT_HOME") or (Path.home() / ".tieout"))


def db_path() -> Path:
    override = os.environ.get("TIEOUT_WORLD_DB")
    return Path(override) if override else tieout_home() / "world.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


def reset_world(path: Path | None = None, today: date | None = None) -> Path:
    """Wipe and rewrite the world from the seed. This is what ``--reset`` calls."""
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    world = build_world(today)
    conn = connect(target)
    try:
        with conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT INTO vendors (id, name, doc) VALUES (?, ?, ?)",
                [(v.id, v.name, v.model_dump_json()) for v in world.vendors],
            )
            conn.executemany(
                "INSERT INTO purchase_orders (id, vendor_id, status, order_date, total, doc)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        p.id,
                        p.vendor_id,
                        p.status,
                        p.order_date.isoformat(),
                        p.total,
                        p.model_dump_json(),
                    )
                    for p in world.purchase_orders
                ],
            )
            conn.executemany(
                "INSERT INTO goods_receipts (id, po_id, vendor_id, received_date, doc)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (g.id, g.po_id, g.vendor_id, g.received_date.isoformat(), g.model_dump_json())
                    for g in world.goods_receipts
                ],
            )
            conn.executemany(
                "INSERT INTO invoices"
                " (id, vendor_id, po_number, status, invoice_date, total, doc)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        i.id,
                        i.vendor_id,
                        i.po_number,
                        i.status,
                        i.invoice_date.isoformat(),
                        i.total,
                        i.model_dump_json(),
                    )
                    for i in world.invoices
                ],
            )
            conn.executemany(
                "INSERT INTO email_threads"
                " (id, vendor_id, po_number, invoice_number, subject, body, doc)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        t.id,
                        t.vendor_id,
                        t.po_number,
                        t.invoice_number,
                        t.subject,
                        "\n\n".join(m.body for m in t.messages),
                        t.model_dump_json(),
                    )
                    for t in world.email_threads
                ],
            )
            conn.executemany(
                "INSERT INTO delivery_notes (id, po_id, vendor_id, ship_date, doc)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (n.id, n.po_id, n.vendor_id, n.ship_date.isoformat(), n.model_dump_json())
                    for n in world.delivery_notes
                ],
            )
            conn.executemany(
                "INSERT INTO world_meta (key, value) VALUES (?, ?)",
                [
                    ("period_start", world.period_start.isoformat()),
                    ("seeded_at", datetime.now().isoformat(timespec="seconds")),
                    ("company", COMPANY_NAME),
                    ("currency", CURRENCY),
                ],
            )
    finally:
        conn.close()
    return target


def ensure_world(path: Path | None = None) -> Path:
    """Seed on first use. Every server calls this at startup."""
    target = path or db_path()
    if not target.exists():
        return reset_world(target)
    return target


# --------------------------------------------------------------------------------------
# Reading it back — the only way erp.py, portal.py and inbox.py touch the data
# --------------------------------------------------------------------------------------


def _rows(sql: str, params: list[Any], path: Path | None = None) -> list[sqlite3.Row]:
    conn = connect(path)
    try:
        return list(conn.execute(sql, params))
    finally:
        conn.close()


def _one(sql: str, params: list[Any], path: Path | None = None) -> sqlite3.Row | None:
    rows = _rows(sql, params, path)
    return rows[0] if rows else None


def world_meta(path: Path | None = None) -> dict[str, str]:
    return {
        row["key"]: row["value"] for row in _rows("SELECT key, value FROM world_meta", [], path)
    }


def list_vendors(q: str | None = None, path: Path | None = None) -> list[Vendor]:
    sql, params = "SELECT doc FROM vendors WHERE 1 = 1", []
    if q:
        sql += " AND (name LIKE ? OR id LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY id"
    return [Vendor.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_vendor(vendor_id: str, path: Path | None = None) -> Vendor | None:
    row = _one("SELECT doc FROM vendors WHERE id = ?", [vendor_id], path)
    return Vendor.model_validate_json(row["doc"]) if row else None


def list_purchase_orders(
    vendor: str | None = None,
    po: str | None = None,
    status: str | None = None,
    path: Path | None = None,
) -> list[PurchaseOrder]:
    sql, params = "SELECT doc FROM purchase_orders WHERE 1 = 1", []
    if vendor:
        sql += " AND vendor_id = ?"
        params.append(vendor)
    if po:
        sql += " AND id = ?"
        params.append(po)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id"
    return [PurchaseOrder.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_purchase_order(po_id: str, path: Path | None = None) -> PurchaseOrder | None:
    row = _one("SELECT doc FROM purchase_orders WHERE id = ?", [po_id], path)
    return PurchaseOrder.model_validate_json(row["doc"]) if row else None


def list_goods_receipts(
    po: str | None = None, vendor: str | None = None, path: Path | None = None
) -> list[GoodsReceipt]:
    sql, params = "SELECT doc FROM goods_receipts WHERE 1 = 1", []
    if po:
        sql += " AND po_id = ?"
        params.append(po)
    if vendor:
        sql += " AND vendor_id = ?"
        params.append(vendor)
    sql += " ORDER BY id"
    return [GoodsReceipt.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_goods_receipt(receipt_id: str, path: Path | None = None) -> GoodsReceipt | None:
    row = _one("SELECT doc FROM goods_receipts WHERE id = ?", [receipt_id], path)
    return GoodsReceipt.model_validate_json(row["doc"]) if row else None


def list_invoices(
    vendor: str | None = None,
    po: str | None = None,
    invoice: str | None = None,
    status: str | None = None,
    path: Path | None = None,
) -> list[Invoice]:
    sql, params = "SELECT doc FROM invoices WHERE 1 = 1", []
    if vendor:
        sql += " AND vendor_id = ?"
        params.append(vendor)
    if po:
        sql += " AND po_number = ?"
        params.append(po)
    if invoice:
        sql += " AND id = ?"
        params.append(invoice)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id"
    return [Invoice.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_invoice(invoice_id: str, path: Path | None = None) -> Invoice | None:
    row = _one("SELECT doc FROM invoices WHERE id = ?", [invoice_id], path)
    return Invoice.model_validate_json(row["doc"]) if row else None


def list_threads(
    vendor: str | None = None,
    po: str | None = None,
    invoice: str | None = None,
    q: str | None = None,
    path: Path | None = None,
) -> list[EmailThread]:
    sql, params = "SELECT doc FROM email_threads WHERE 1 = 1", []
    if vendor:
        sql += " AND vendor_id = ?"
        params.append(vendor)
    if po:
        sql += " AND po_number = ?"
        params.append(po)
    if invoice:
        sql += " AND invoice_number = ?"
        params.append(invoice)
    if q:
        sql += " AND (subject LIKE ? OR body LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY id"
    return [EmailThread.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_thread(thread_id: str, path: Path | None = None) -> EmailThread | None:
    row = _one("SELECT doc FROM email_threads WHERE id = ?", [thread_id], path)
    return EmailThread.model_validate_json(row["doc"]) if row else None


def list_delivery_notes(vendor: str | None = None, path: Path | None = None) -> list[DeliveryNote]:
    sql, params = "SELECT doc FROM delivery_notes WHERE 1 = 1", []
    if vendor:
        sql += " AND vendor_id = ?"
        params.append(vendor)
    sql += " ORDER BY po_id"
    return [DeliveryNote.model_validate_json(row["doc"]) for row in _rows(sql, params, path)]


def get_delivery_note(po_id: str, path: Path | None = None) -> DeliveryNote | None:
    row = _one("SELECT doc FROM delivery_notes WHERE po_id = ?", [po_id], path)
    return DeliveryNote.model_validate_json(row["doc"]) if row else None


def portal_credentials() -> tuple[str, str]:
    """The AP team's own login on the supplier network. Env wins; the demo default is public."""
    return (
        os.environ.get("PORTAL_USER") or DEFAULT_PORTAL_USER,
        os.environ.get("PORTAL_PASS") or DEFAULT_PORTAL_PASS,
    )


def summary(path: Path | None = None) -> dict[str, Any]:
    """What ``--reset`` prints, so a human can see the world is really there."""
    conn = connect(path)
    try:
        counts = {
            table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
            for table in (
                "vendors",
                "purchase_orders",
                "goods_receipts",
                "invoices",
                "email_threads",
                "delivery_notes",
            )
        }
    finally:
        conn.close()
    counts["seeded_exceptions"] = len(SEED_EXCEPTIONS)
    return {"database": str(path or db_path()), "meta": world_meta(path), "counts": counts}


if __name__ == "__main__":  # pragma: no cover - convenience only
    print(json.dumps(summary(reset_world()), indent=2))
