"""The vendor portal: the source with no API. The ONLY file in Tieout that imports Playwright.

Every other integration in accounts payable has an endpoint. This one has a login form, and
that is exactly why the work stays manual: a controller signs in with a browser and reads a
delivery note with their eyes. Tieout does the same thing, with a real browser, on the real
page, and brings back a screenshot so the evidence is something a human can look at.

Three things this file is careful about:

* **Its own thread.** Playwright's sync API refuses to run inside an asyncio loop and binds
  its objects to the thread that made them. The browser therefore runs on a worker thread and
  hands back a plain pydantic object; the audit trail is only ever written on the caller's
  thread.
* **Sessions persist.** After a successful sign-in the context is saved with
  ``storage_state`` to ``~/.tieout/sessions/vendorlink.json``. The next investigation loads
  it and never sees the login page. That is tier 2 of the production auth story in
  ``backend/CLAUDE.md``, built rather than claimed — and it is why Tieout deliberately does
  **not** sign out at the end.
* **Credentials come from the environment**, and never touch a stored pack or a screenshot.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:  # the real import happens inside the worker thread, in _visit
    from playwright.sync_api import Page

from .. import load_env, tieout_home
from ..evidence import EvidenceTrail
from ..models import ExceptionCase, FactKind, Figures, Source

DEFAULT_BASE_URL = "http://127.0.0.1:8702"
# The demo world's own buyer account, printed on its own sign-in page. Env always wins.
DEFAULT_PORTAL_USER = "ap-bot@kestrelmfg.com"
DEFAULT_PORTAL_PASS = "tieout-demo"
SESSION_NAME = "vendorlink"
NAV_TIMEOUT_MS = 20_000


def default_base_url() -> str:
    load_env()
    return os.environ.get("TIEOUT_PORTAL_URL") or DEFAULT_BASE_URL


def credentials() -> tuple[str, str]:
    load_env()
    return (
        os.environ.get("PORTAL_USER") or DEFAULT_PORTAL_USER,
        os.environ.get("PORTAL_PASS") or DEFAULT_PORTAL_PASS,
    )


def headless() -> bool:
    """``HEADLESS=0`` puts a real window on screen. That is the shot the video needs."""
    load_env()
    return os.environ.get("HEADLESS", "1").strip() not in {"0", "false", "no"}


def session_file() -> Path:
    return tieout_home() / "sessions" / f"{SESSION_NAME}.json"


def screenshot_dir() -> Path:
    return tieout_home() / "screenshots"


def forget_session() -> None:
    """Throw the saved cookie away. ``tieout reset`` calls this so a demo starts cold."""
    path = session_file()
    if path.exists():
        path.unlink()


# --------------------------------------------------------------------------------------
# What the browser brings back
# --------------------------------------------------------------------------------------


class PortalLine(BaseModel):
    sku: str
    description: str = ""
    qty_ordered: int = 0
    qty_shipped: int = 0


class PortalObservation(BaseModel):
    url: str
    found: bool
    signed_in: bool = False
    reused_session: bool = False
    screenshot: str = ""
    document_id: str = ""
    ship_date: date | None = None
    carrier: str = ""
    tracking: str = ""
    note: str = ""
    page_text: str = ""
    lines: list[PortalLine] = Field(default_factory=list)

    @property
    def qty_shipped(self) -> int:
        return sum(line.qty_shipped for line in self.lines)

    @property
    def qty_ordered(self) -> int:
        return sum(line.qty_ordered for line in self.lines)


# --------------------------------------------------------------------------------------
# The browser, on its own thread
# --------------------------------------------------------------------------------------


def visit(case: ExceptionCase, *, base_url: str | None = None) -> PortalObservation:
    """Open the portal for this exception and come back with what was on the screen."""
    target = (base_url or default_base_url()).rstrip("/")
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="tieout-portal") as pool:
        return pool.submit(_visit, case, target).result()


def _visit(case: ExceptionCase, base_url: str) -> PortalObservation:
    from playwright.sync_api import sync_playwright  # imported here: this file owns Playwright

    user, password = credentials()
    saved = session_file()
    reuse = saved.is_file()
    screenshot_dir().mkdir(parents=True, exist_ok=True)
    saved.parent.mkdir(parents=True, exist_ok=True)

    if case.po_id:
        path = f"/orders/{case.po_id}/delivery-note"
    else:
        path = f"/orders?q={case.invoice_id}"
    url = f"{base_url}{path}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless())
        try:
            context = browser.new_context(storage_state=str(saved) if reuse else None)
            page = context.new_page()
            page.set_default_timeout(NAV_TIMEOUT_MS)
            page.goto(url, wait_until="domcontentloaded")

            signed_in = False
            if "/login" in page.url:
                # Either the first ever run, or the saved cookie has expired. Sign in and
                # save the session, so the next investigation walks straight in.
                page.fill("#username", user)
                page.fill("#password", password)
                page.click("button.primary")
                page.wait_for_load_state("domcontentloaded")
                context.storage_state(path=str(saved))
                signed_in = True
                reuse = False
                if page.url.rstrip("/") != url.rstrip("/"):
                    page.goto(url, wait_until="domcontentloaded")

            shot = screenshot_dir() / f"{case.id}-{case.po_id or case.invoice_id}.png"
            page.screenshot(path=str(shot), full_page=True)

            observation = _read_page(page, url, str(shot))
            observation.signed_in = signed_in
            observation.reused_session = reuse and not signed_in
            return observation
        finally:
            browser.close()


def _read_page(page: Page, url: str, shot: str) -> PortalObservation:
    """Read the delivery note off the rendered page, the same way a person reads it."""
    text = page.inner_text("body")
    heading = page.locator("h1").first.inner_text().strip()

    if "Delivery note" not in heading:
        return PortalObservation(url=url, found=False, screenshot=shot, page_text=text)

    values = [element.inner_text().strip() for element in page.locator(".meta div strong").all()]
    ship_date = _parse_date(values[1]) if len(values) > 1 else None

    lines: list[PortalLine] = []
    for row in page.locator("table tbody tr").all():
        cells = [cell.inner_text().strip() for cell in row.locator("td").all()]
        if len(cells) < 5:
            continue
        lines.append(
            PortalLine(
                sku=cells[1],
                description=cells[2].split("\n")[0].strip(),
                qty_ordered=_parse_int(cells[3]),
                qty_shipped=_parse_int(cells[4]),
            )
        )

    note = ""
    note_box = page.locator(".note")
    if note_box.count():
        raw_note = note_box.first.inner_text().strip().splitlines()
        note = " ".join(part.strip() for part in raw_note[1:]).strip()

    return PortalObservation(
        url=url,
        found=True,
        screenshot=shot,
        document_id=heading.replace("Delivery note", "").strip(),
        ship_date=ship_date,
        carrier=values[2] if len(values) > 2 else "",
        tracking=values[3] if len(values) > 3 else "",
        note=note,
        page_text=text,
        lines=lines,
    )


def _parse_int(value: str) -> int:
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else 0


def _parse_date(value: str) -> date | None:
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------------------
# Collecting evidence
# --------------------------------------------------------------------------------------


def collect(trail: EvidenceTrail, case: ExceptionCase, *, base_url: str | None = None) -> None:
    """Sign in if we have to, read the shipping document, put it on the trail with a picture."""
    target = (base_url or default_base_url()).rstrip("/")
    user, _ = credentials()
    trail.looked(
        source=Source.PORTAL,
        action="opened the VendorLink supplier portal in a browser",
        locator=target,
        found=True,
        note="this supplier network has no API",
    )

    observation = visit(case, base_url=target)

    if observation.signed_in:
        trail.looked(
            source=Source.PORTAL,
            action=f"signed in to VendorLink as {user}",
            locator=f"{target}/login",
            found=True,
            note="session saved, so the next investigation skips the login",
        )
    elif observation.reused_session:
        trail.looked(
            source=Source.PORTAL,
            action="reused the saved VendorLink session — no sign-in needed",
            locator=str(session_file()),
            found=True,
        )

    if not observation.found:
        trail.looked(
            source=Source.PORTAL,
            action=f"searched VendorLink for {case.po_id or case.invoice_id}",
            locator=observation.url,
            found=False,
            note="no shipping document has been published",
        )
        trail.record(
            source=Source.PORTAL,
            kind=FactKind.PORTAL_ABSENCE,
            statement=(
                f"VendorLink has no shipping document for {case.po_id or case.invoice_id} "
                f"({case.vendor_name}); the supplier is not on the network."
            ),
            locator=observation.url,
            raw=observation.page_text,
            screenshot=observation.screenshot,
        )
        return

    trail.looked(
        source=Source.PORTAL,
        action=f"opened delivery note {observation.document_id}",
        locator=observation.url,
        found=True,
    )
    detail = ", ".join(
        f"{line.qty_shipped} of {line.qty_ordered} x {line.sku}" for line in observation.lines
    )
    shipped_on = (
        f" and despatched on {observation.ship_date.isoformat()}" if observation.ship_date else ""
    )
    trail.record(
        source=Source.PORTAL,
        kind=FactKind.DELIVERY_NOTE,
        statement=(
            f"Delivery note {observation.document_id} on VendorLink shows {detail} "
            f"shipped{shipped_on}"
            + (f" — supplier note: {observation.note}" if observation.note else ".")
        ),
        locator=observation.url,
        raw=observation.page_text,
        figures=Figures(
            qty_ordered=observation.qty_ordered,
            qty_shipped=observation.qty_shipped,
            event_date=observation.ship_date,
        ),
        screenshot=observation.screenshot,
    )
