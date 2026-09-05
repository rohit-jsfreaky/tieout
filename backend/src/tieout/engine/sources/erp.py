"""The ERP: the ledger of record, read over its JSON API.

The engine parses the ERP's responses into its own shapes rather than importing the world's
models. That is not ceremony — it is how this code would be written against NetSuite or SAP,
and it means nothing in ``engine/`` can accidentally reach into the seed and read the
answers it is supposed to find for itself.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ..evidence import EvidenceTrail
from ..models import ExceptionCase, ExceptionKind, FactKind, Figures, Source

DEFAULT_BASE_URL = "http://127.0.0.1:8701"
TIMEOUT_SECONDS = 15.0


def default_base_url() -> str:
    return os.environ.get("TIEOUT_ERP_URL") or DEFAULT_BASE_URL


# --------------------------------------------------------------------------------------
# What the ERP hands back
# --------------------------------------------------------------------------------------


class ErpVendor(BaseModel):
    id: str
    name: str
    contact_email: str = ""
    payment_terms: str = ""


class ErpOrderLine(BaseModel):
    line_no: int
    sku: str
    description: str = ""
    qty_ordered: int = 0
    unit_price: float = 0.0


class ErpPurchaseOrder(BaseModel):
    id: str
    vendor_id: str
    order_date: date
    status: str
    total: float
    currency: str = "USD"
    lines: list[ErpOrderLine] = Field(default_factory=list)


class ErpReceiptLine(BaseModel):
    line_no: int
    sku: str
    qty_received: int = 0


class ErpGoodsReceipt(BaseModel):
    id: str
    po_id: str
    vendor_id: str
    received_date: date
    lines: list[ErpReceiptLine] = Field(default_factory=list)


class ErpInvoiceLine(BaseModel):
    line_no: int
    sku: str
    description: str = ""
    qty: int = 0
    unit_price: float = 0.0
    amount: float = 0.0


class ErpInvoice(BaseModel):
    id: str
    vendor_id: str
    po_number: str | None = None
    invoice_date: date
    due_date: date | None = None
    status: str = "open"
    total: float
    currency: str = "USD"
    lines: list[ErpInvoiceLine] = Field(default_factory=list)


# --------------------------------------------------------------------------------------
# The client
# --------------------------------------------------------------------------------------


class ErpClient:
    """Read-only access to the ledger.

    ``client`` is injectable so the tests can drive the ERP's ASGI app in-process — still
    through its real routes, just without a socket.
    """

    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None) -> None:
        self.base_url = (base_url or default_base_url()).rstrip("/")
        self._client = client
        self._owns_client = client is None

    def __enter__(self) -> ErpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()
            self._client = None

    @property
    def http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, timeout=TIMEOUT_SECONDS)
        return self._client

    def url(self, path: str) -> str:
        """The locator that goes on a Fact: anyone can paste it into curl."""
        return f"{self.base_url}{path}"

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        query = {key: value for key, value in params.items() if value is not None}
        response = self.http.get(path, params=query)
        response.raise_for_status()
        return response.json()

    # -- endpoints ----------------------------------------------------------------------

    def period_start(self) -> date:
        """The month the books are open for. The evidence window is measured from here."""
        meta = self._get("/health").get("meta", {})
        return date.fromisoformat(meta["period_start"])

    def vendors(self) -> list[ErpVendor]:
        return [ErpVendor.model_validate(item) for item in self._get("/vendors")["items"]]

    def invoices(self, **filters: Any) -> list[ErpInvoice]:
        return [
            ErpInvoice.model_validate(item) for item in self._get("/invoices", **filters)["items"]
        ]

    def invoice(self, invoice_id: str) -> ErpInvoice:
        return ErpInvoice.model_validate(self._get(f"/invoices/{invoice_id}"))

    def purchase_orders(self, **filters: Any) -> list[ErpPurchaseOrder]:
        return [
            ErpPurchaseOrder.model_validate(item)
            for item in self._get("/purchase_orders", **filters)["items"]
        ]

    def purchase_order(self, po_id: str) -> ErpPurchaseOrder:
        return ErpPurchaseOrder.model_validate(self._get(f"/purchase_orders/{po_id}"))

    def goods_receipts(self, **filters: Any) -> list[ErpGoodsReceipt]:
        return [
            ErpGoodsReceipt.model_validate(item)
            for item in self._get("/goods_receipts", **filters)["items"]
        ]


# --------------------------------------------------------------------------------------
# Collecting evidence
# --------------------------------------------------------------------------------------


def collect(trail: EvidenceTrail, case: ExceptionCase, erp: ErpClient) -> None:
    """Put the ledger's side of the story on the trail: the invoice, the order, the receipt."""
    _record_invoice(trail, case, erp)
    if case.kind is ExceptionKind.MISSING_PO:
        _record_candidate_po(trail, case, erp)
    else:
        _record_purchase_order(trail, case, erp)
    _record_receipts(trail, case, erp)


def _record_invoice(trail: EvidenceTrail, case: ExceptionCase, erp: ErpClient) -> None:
    path = f"/invoices/{case.invoice_id}"
    invoice = erp.invoice(case.invoice_id)
    trail.looked(
        source=Source.ERP,
        action=f"opened invoice {case.invoice_id} in the ERP",
        locator=erp.url(path),
        found=True,
    )
    detail = ", ".join(
        f"{line.qty} x {line.sku} at {line.unit_price:,.2f}" for line in invoice.lines
    )
    trail.record(
        source=Source.ERP,
        kind=FactKind.INVOICE,
        statement=(
            f"{case.vendor_name} billed {invoice.total:,.2f} {invoice.currency} on invoice "
            f"{invoice.id} dated {invoice.invoice_date.isoformat()} ({detail})."
        ),
        locator=erp.url(path),
        raw=invoice.model_dump_json(),
        figures=Figures(
            qty_billed=sum(line.qty for line in invoice.lines),
            amount=invoice.total,
            event_date=invoice.invoice_date,
            unit_price=invoice.lines[0].unit_price if invoice.lines else None,
        ),
    )


def _record_purchase_order(trail: EvidenceTrail, case: ExceptionCase, erp: ErpClient) -> None:
    if case.po_id is None:
        trail.looked(
            source=Source.ERP,
            action="looked for a purchase order on the invoice",
            locator=erp.url("/purchase_orders"),
            found=False,
            note="the invoice carries no PO number",
        )
        return
    path = f"/purchase_orders/{case.po_id}"
    try:
        po = erp.purchase_order(case.po_id)
    except httpx.HTTPStatusError:
        trail.looked(
            source=Source.ERP,
            action=f"looked for purchase order {case.po_id}",
            locator=erp.url(path),
            found=False,
            note="the invoice names an order the ERP does not have",
        )
        return
    trail.looked(
        source=Source.ERP,
        action=f"opened purchase order {po.id}",
        locator=erp.url(path),
        found=True,
    )
    detail = ", ".join(
        f"{line.qty_ordered} x {line.sku} at {line.unit_price:,.2f}" for line in po.lines
    )
    trail.record(
        source=Source.ERP,
        kind=FactKind.PURCHASE_ORDER,
        statement=(
            f"Purchase order {po.id} was raised on {po.order_date.isoformat()} for "
            f"{po.total:,.2f} {po.currency} ({detail})."
        ),
        locator=erp.url(path),
        raw=po.model_dump_json(),
        figures=Figures(
            qty_ordered=sum(line.qty_ordered for line in po.lines),
            unit_price=po.lines[0].unit_price if po.lines else None,
            amount=po.total,
            event_date=po.order_date,
        ),
    )


def _record_candidate_po(trail: EvidenceTrail, case: ExceptionCase, erp: ErpClient) -> None:
    """For a missing-PO invoice, the open orders for this supplier are the evidence."""
    path = "/purchase_orders"
    open_orders = erp.purchase_orders(vendor=case.vendor_id, status="open")
    trail.looked(
        source=Source.ERP,
        action=f"searched the ERP for open orders from {case.vendor_name}",
        locator=erp.url(f"{path}?vendor={case.vendor_id}&status=open"),
        found=bool(open_orders),
        note=f"{len(open_orders)} open order(s)",
    )
    if case.po_id is None:
        return
    candidate = next((po for po in open_orders if po.id == case.po_id), None)
    if candidate is None:
        return
    trail.record(
        source=Source.ERP,
        kind=FactKind.CANDIDATE_PO,
        statement=(
            f"{candidate.id} is the only open order for {case.vendor_name} that matches the "
            f"invoice: {candidate.total:,.2f} {candidate.currency} raised on "
            f"{candidate.order_date.isoformat()}, against an invoice for {case.amount:,.2f} "
            f"dated {case.invoice_date.isoformat()}."
        ),
        locator=erp.url(f"{path}/{candidate.id}"),
        raw=candidate.model_dump_json(),
        figures=Figures(
            qty_ordered=sum(line.qty_ordered for line in candidate.lines),
            amount=candidate.total,
            event_date=candidate.order_date,
        ),
    )


def _record_receipts(trail: EvidenceTrail, case: ExceptionCase, erp: ErpClient) -> None:
    if case.po_id is None:
        trail.looked(
            source=Source.ERP,
            action=f"searched goods receipts for {case.vendor_name}",
            locator=erp.url(f"/goods_receipts?vendor={case.vendor_id}"),
            found=bool(erp.goods_receipts(vendor=case.vendor_id)),
            note="nothing to match the invoice against without an order number",
        )
        return

    receipts = erp.goods_receipts(po=case.po_id)
    locator = erp.url(f"/goods_receipts?po={case.po_id}")
    trail.looked(
        source=Source.ERP,
        action=f"searched goods receipts against {case.po_id}",
        locator=locator,
        found=bool(receipts),
        note="" if receipts else "the warehouse never booked this order in",
    )
    for receipt in receipts:
        detail = ", ".join(f"{line.qty_received} x {line.sku}" for line in receipt.lines)
        trail.record(
            source=Source.ERP,
            kind=FactKind.GOODS_RECEIPT,
            statement=(
                f"Goods receipt {receipt.id} records {detail} received on "
                f"{receipt.received_date.isoformat()}."
            ),
            locator=locator,
            raw=receipt.model_dump_json(),
            figures=Figures(
                qty_received=sum(line.qty_received for line in receipt.lines),
                event_date=receipt.received_date,
            ),
        )
