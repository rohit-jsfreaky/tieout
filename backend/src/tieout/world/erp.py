"""The ERP. Read-only JSON over the seeded ledger, on :8701.

Four tables — vendors, purchase orders, goods receipts, invoices — each with a list endpoint
that filters and a get endpoint. Nothing clever: a real ERP's API is exactly this boring, and
the engine's job is to read it, not to be impressed by it.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from . import seed, seeded_lifespan

PORT = 8701
TITLE = f"{seed.COMPANY_NAME} ERP"

app = FastAPI(
    title=TITLE,
    version="1.0",
    description="Ledger of record. Read-only.",
    lifespan=seeded_lifespan,
)


def _page(items: list[Any]) -> dict[str, Any]:
    """Every list endpoint answers the same shape, so a count is always one field away."""
    return {"count": len(items), "items": [item.model_dump(mode="json") for item in items]}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "erp", "status": "ok", "meta": seed.world_meta()}


@app.get("/vendors")
def vendors(q: str | None = Query(default=None)) -> dict[str, Any]:
    return _page(seed.list_vendors(q=q))


@app.get("/vendors/{vendor_id}")
def vendor(vendor_id: str) -> dict[str, Any]:
    found = seed.get_vendor(vendor_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no vendor {vendor_id}")
    return found.model_dump(mode="json")


@app.get("/purchase_orders")
def purchase_orders(
    vendor: str | None = Query(default=None),
    po: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return _page(seed.list_purchase_orders(vendor=vendor, po=po, status=status))


@app.get("/purchase_orders/{po_id}")
def purchase_order(po_id: str) -> dict[str, Any]:
    found = seed.get_purchase_order(po_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no purchase order {po_id}")
    return found.model_dump(mode="json")


@app.get("/goods_receipts")
def goods_receipts(
    po: str | None = Query(default=None),
    vendor: str | None = Query(default=None),
) -> dict[str, Any]:
    return _page(seed.list_goods_receipts(po=po, vendor=vendor))


@app.get("/goods_receipts/{receipt_id}")
def goods_receipt(receipt_id: str) -> dict[str, Any]:
    found = seed.get_goods_receipt(receipt_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no goods receipt {receipt_id}")
    return found.model_dump(mode="json")


@app.get("/invoices")
def invoices(
    vendor: str | None = Query(default=None),
    po: str | None = Query(default=None),
    invoice: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return _page(seed.list_invoices(vendor=vendor, po=po, invoice=invoice, status=status))


@app.get("/invoices/{invoice_id}")
def invoice(invoice_id: str) -> dict[str, Any]:
    found = seed.get_invoice(invoice_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no invoice {invoice_id}")
    return found.model_dump(mode="json")
