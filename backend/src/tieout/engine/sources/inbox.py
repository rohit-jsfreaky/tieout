"""The AP shared mailbox: the source that is written in English rather than in columns.

This is the one place the language model touches evidence, and it is fenced in:
``model.facts_from_text`` may only turn a vendor's own words into short claims, each one
carried back with the email it came from so a controller can read the original. Anything the
model returns that ``evidence.py`` will not accept — a date outside the open period, an empty
claim — is dropped and recorded as a dropped claim, not quietly kept.

If the model is unavailable, the thread still lands on the trail as a fact written by code.
A source that disappears when an API is down is not a source.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from .. import model as llm
from ..evidence import EvidenceError, EvidenceTrail
from ..models import ExceptionCase, FactKind, Figures, Source

DEFAULT_BASE_URL = "http://127.0.0.1:8703"
TIMEOUT_SECONDS = 15.0
MAX_THREADS_READ = 2
MAX_FACTS_PER_THREAD = 3


def default_base_url() -> str:
    return os.environ.get("TIEOUT_INBOX_URL") or DEFAULT_BASE_URL


class InboxMessage(BaseModel):
    sender: str
    recipient: str = ""
    sent_at: datetime
    body: str


class InboxThread(BaseModel):
    id: str
    subject: str
    vendor_id: str
    po_number: str | None = None
    invoice_number: str | None = None
    messages: list[InboxMessage] = Field(default_factory=list)


class InboxClient:
    """Search the mailbox the way a person does: by order, by invoice, by supplier."""

    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None) -> None:
        self.base_url = (base_url or default_base_url()).rstrip("/")
        self._client = client
        self._owns_client = client is None

    def __enter__(self) -> InboxClient:
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
        return f"{self.base_url}{path}"

    def threads(self, **filters: Any) -> list[InboxThread]:
        query = {key: value for key, value in filters.items() if value}
        response = self.http.get("/threads", params=query)
        response.raise_for_status()
        return [InboxThread.model_validate(item) for item in response.json()["items"]]


def collect(
    trail: EvidenceTrail, case: ExceptionCase, inbox: InboxClient, *, today: date | None = None
) -> None:
    """Search for correspondence about this exception and read whatever turns up."""
    today = today or date.today()
    seen: set[str] = set()
    found: list[tuple[InboxThread, str]] = []

    for description, params in _searches(case):
        threads = inbox.threads(**params)
        query = "&".join(f"{key}={value}" for key, value in params.items())
        locator = inbox.url(f"/threads?{query}")
        trail.looked(
            source=Source.INBOX,
            action=f"searched the AP mailbox {description}",
            locator=locator,
            found=bool(threads),
            note="" if threads else "no correspondence",
        )
        for thread in threads:
            if thread.id not in seen and len(found) < MAX_THREADS_READ:
                seen.add(thread.id)
                found.append((thread, inbox.url(f"/threads/{thread.id}")))
        if found:
            break

    for thread, locator in found:
        _read_thread(trail, case, thread, locator, today)


def _searches(case: ExceptionCase) -> list[tuple[str, dict[str, str]]]:
    """Narrowest search first. The supplier-wide sweep is the last resort."""
    searches: list[tuple[str, dict[str, str]]] = []
    if case.po_id:
        searches.append((f"for order {case.po_id}", {"po": case.po_id}))
    searches.append((f"for invoice {case.invoice_id}", {"invoice": case.invoice_id}))
    searches.append((f"for anything from {case.vendor_name}", {"vendor": case.vendor_id}))
    return searches


def _read_thread(
    trail: EvidenceTrail,
    case: ExceptionCase,
    thread: InboxThread,
    locator: str,
    today: date,
) -> None:
    body = "\n\n".join(message.body for message in thread.messages)
    sender = thread.messages[0].sender if thread.messages else case.vendor_name
    trail.looked(
        source=Source.INBOX,
        action=f'opened the thread "{thread.subject}" from {sender}',
        locator=locator,
        found=True,
    )

    try:
        extracted = llm.facts_from_text(
            body,
            subject=thread.subject,
            sender=sender,
            context=(
                f"Invoice {case.invoice_id} from {case.vendor_name} did not tie out: "
                f"{case.headline}"
            ),
            today=today,
        )
    except llm.ModelError as exc:
        trail.warn(f"reading {thread.id} without the model: {exc}")
        _record_verbatim(trail, thread, sender, body, locator)
        return

    kept = 0
    for item in extracted[:MAX_FACTS_PER_THREAD]:
        try:
            trail.record(
                source=Source.INBOX,
                kind=FactKind.VENDOR_EMAIL,
                statement=item.statement,
                locator=locator,
                raw=body,
                figures=item.figures,
                extracted_by=llm.label(),
            )
        except EvidenceError as exc:
            # The model got something wrong. Say so on the trail; never keep it.
            trail.looked(
                source=Source.INBOX,
                action=f"dropped a claim read out of {thread.id}",
                locator=locator,
                found=False,
                note=str(exc),
            )
            continue
        kept += 1

    if kept == 0:
        _record_verbatim(trail, thread, sender, body, locator)


def _record_verbatim(
    trail: EvidenceTrail, thread: InboxThread, sender: str, body: str, locator: str
) -> None:
    """No usable extraction: put the vendor's own words on the trail, written by code."""
    first_line = next((line.strip() for line in body.splitlines() if line.strip()), body.strip())
    sent_at = thread.messages[0].sent_at.date() if thread.messages else None
    trail.record(
        source=Source.INBOX,
        kind=FactKind.VENDOR_EMAIL,
        statement=(f'{sender} wrote "{thread.subject}" to accounts payable: {first_line[:180]}'),
        locator=locator,
        raw=body,
        figures=Figures(event_date=sent_at),
    )
