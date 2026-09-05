"""The AP shared mailbox, on :8703. JSON threads, searchable the way a person searches.

Three of the five exceptions have a vendor email that explains them. E5 has none, and that
silence is data: it is one of the reasons the engine refuses instead of guessing.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from . import seed, seeded_lifespan

PORT = 8703

app = FastAPI(
    title=f"{seed.COMPANY_NAME} AP mailbox",
    version="1.0",
    description="Vendor correspondence. Read-only.",
    lifespan=seeded_lifespan,
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "inbox", "status": "ok", "mailbox": f"ap@{seed.COMPANY_DOMAIN}"}


@app.get("/threads")
def threads(
    vendor: str | None = Query(default=None),
    po: str | None = Query(default=None),
    invoice: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> dict[str, Any]:
    found = seed.list_threads(vendor=vendor, po=po, invoice=invoice, q=q)
    return {
        "count": len(found),
        "query": {"vendor": vendor, "po": po, "invoice": invoice, "q": q},
        "items": [thread.model_dump(mode="json") for thread in found],
    }


@app.get("/threads/{thread_id}")
def thread(thread_id: str) -> dict[str, Any]:
    found = seed.get_thread(thread_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no thread {thread_id}")
    return found.model_dump(mode="json")
