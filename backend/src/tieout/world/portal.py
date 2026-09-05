"""VendorLink, the supplier network portal, on :8702. HTML only — no API, on purpose.

This is the source with no integration. Kestrel's AP team has one account here and reads
delivery notes by hand. Tieout signs in the same way, with a browser, because there is no
other way in.

The login is real: a form post, a session cookie, and a redirect back to the login page for
anyone without one. Two pages get visual care — the login and the delivery note — because
those are the two a judge sees.
"""

from __future__ import annotations

import secrets
from datetime import date, datetime
from html import escape

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from . import seed, seeded_lifespan

PORT = 8702
SESSION_COOKIE = "vendorlink_session"

app = FastAPI(
    title=f"{seed.PORTAL_NAME} supplier network",
    version="1.0",
    description="Delivery notes and shipping documents. No API.",
    lifespan=seeded_lifespan,
)

# token -> {"user": ..., "signed_in_at": ...}. In memory: this is a fixture, not a bank.
SESSIONS: dict[str, dict[str, str]] = {}

CSS = """
:root {
  --ink: #10202e; --muted: #5d7285; --line: #dde5ec; --paper: #ffffff;
  --bg: #eef2f6; --navy: #123651; --amber: #b26a00; --amber-bg: #fdf3e2;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.55 "Segoe UI", -apple-system, Roboto, Helvetica, Arial, sans-serif;
}
a { color: var(--navy); }
.topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: var(--navy); color: #eaf1f6; padding: 12px 28px;
}
.brand { display: flex; align-items: center; gap: 10px; font-weight: 600; letter-spacing: .2px; }
.mark {
  display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 7px;
  background: #eaf1f6; color: var(--navy); font-weight: 700; font-size: 13px;
}
.topbar .sub { color: #a9c1d3; font-weight: 400; font-size: 13px; }
.session { display: flex; align-items: center; gap: 12px; font-size: 13px; color: #cfe0ec; }
.linkbtn {
  background: none; border: 1px solid #3d6580; color: #eaf1f6; border-radius: 6px;
  padding: 5px 11px; font-size: 13px; cursor: pointer;
}
main { max-width: 980px; margin: 32px auto 56px; padding: 0 24px; }
h1 { font-size: 22px; margin: 0 0 4px; }
.lede { color: var(--muted); margin: 0 0 22px; }
.card {
  background: var(--paper); border: 1px solid var(--line); border-radius: 12px;
  padding: 22px 24px; box-shadow: 0 1px 2px rgba(16,32,46,.05);
}
.card + .card { margin-top: 18px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th {
  text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: .06em;
  color: var(--muted); border-bottom: 1px solid var(--line); padding: 0 10px 8px;
}
td { padding: 11px 10px; border-bottom: 1px solid #f0f4f7; vertical-align: top; }
tr:last-child td { border-bottom: none; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.meta { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 22px; }
.meta div span { display: block; font-size: 12px; text-transform: uppercase;
                 letter-spacing: .06em; color: var(--muted); margin-bottom: 3px; }
.meta div strong { font-weight: 600; }
.chip {
  display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px;
  font-weight: 600; background: #e8f0f5; color: var(--navy);
}
.chip.short { background: var(--amber-bg); color: var(--amber); }
.note {
  margin-top: 20px; padding: 14px 16px; border-radius: 10px; background: var(--amber-bg);
  border: 1px solid #f0dcb8; color: #6d4a08;
}
.note span { display: block; font-size: 12px; text-transform: uppercase;
             letter-spacing: .06em; color: var(--amber); margin-bottom: 4px; }
form.search { display: flex; gap: 10px; margin-bottom: 18px; }
input[type=text], input[type=password] {
  width: 100%; padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px;
  font: inherit; background: #fbfdfe;
}
button.primary {
  background: var(--navy); color: #fff; border: none; border-radius: 8px; padding: 10px 18px;
  font: inherit; font-weight: 600; cursor: pointer;
}
.signin { max-width: 400px; margin: 72px auto; }
.signin .card { padding: 30px 30px 26px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.hint { margin-top: 18px; font-size: 12.5px; color: var(--muted); }
.error {
  margin-bottom: 16px; padding: 10px 12px; border-radius: 8px; background: #fdecec;
  border: 1px solid #f4c9c9; color: #97231f; font-size: 13.5px;
}
footer { max-width: 980px; margin: 0 auto 40px; padding: 0 24px; color: var(--muted);
         font-size: 12.5px; }
"""


def _page(title: str, body: str, user: str | None = None) -> str:
    session_bar = (
        f'<div class="session">Signed in as {escape(user)}'
        '<form method="post" action="/logout">'
        '<button class="linkbtn" type="submit">Sign out</button></form></div>'
        if user
        else '<div class="session">Not signed in</div>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — {escape(seed.PORTAL_NAME)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="topbar">
  <div class="brand"><span class="mark">VL</span>{escape(seed.PORTAL_NAME)}
    <span class="sub">{escape(seed.PORTAL_TAGLINE)}</span></div>
  {session_bar}
</header>
<main>{body}</main>
<footer>{escape(seed.PORTAL_NAME)} · documents are retained for 24 months ·
support@vendorlink.example</footer>
</body>
</html>"""


def _current_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    session = SESSIONS.get(token) if token else None
    return session["user"] if session else None


def _sign_in_redirect(request: Request) -> RedirectResponse:
    """No session, no documents. The engine has to sign in like a person."""
    return RedirectResponse(f"/login?next={request.url.path}", status_code=303)


def _fmt_date(value: date | datetime) -> str:
    return f"{value.day} {value:%B %Y}"


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse("/orders", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_form(next: str = "/orders", error: str | None = None) -> HTMLResponse:
    user, _ = seed.portal_credentials()
    error_html = f'<div class="error">{escape(error)}</div>' if error else ""
    body = f"""
<div class="signin">
  <div class="card">
    <h1>Sign in</h1>
    <p class="lede">Use your buyer account to view supplier documents.</p>
    {error_html}
    <form method="post" action="/login">
      <input type="hidden" name="next" value="{escape(next)}">
      <div class="field">
        <label for="username">Email</label>
        <input id="username" type="text" name="username" autocomplete="username" autofocus>
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input id="password" type="password" name="password" autocomplete="current-password">
      </div>
      <button class="primary" type="submit">Sign in</button>
    </form>
    <p class="hint">Demo buyer account: <strong>{escape(user)}</strong> — the password is in
    the project's <code>.env.example</code>.</p>
  </div>
</div>"""
    return HTMLResponse(_page("Sign in", body))


@app.post("/login")
def login(
    username: str = Form(default=""),
    password: str = Form(default=""),
    next: str = Form(default="/orders"),
) -> Response:
    expected_user, expected_pass = seed.portal_credentials()
    ok = secrets.compare_digest(username.strip(), expected_user) and secrets.compare_digest(
        password, expected_pass
    )
    if not ok:
        return RedirectResponse(
            f"/login?next={next}&error=Those+details+were+not+recognised.", status_code=303
        )
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {
        "user": expected_user,
        "signed_in_at": datetime.now().isoformat(timespec="seconds"),
    }
    response = RedirectResponse(next or "/orders", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", path="/")
    return response


@app.post("/logout")
def logout(request: Request) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        SESSIONS.pop(token, None)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/orders", response_class=HTMLResponse)
def orders(request: Request, q: str | None = None) -> Response:
    user = _current_user(request)
    if user is None:
        return _sign_in_redirect(request)

    notes = seed.list_delivery_notes()
    needle = (q or "").strip().lower()
    if needle:
        notes = [
            note
            for note in notes
            if needle in note.po_id.lower()
            or needle in note.id.lower()
            or any(needle in line.sku.lower() for line in note.lines)
        ]

    vendors = {vendor.id: vendor.name for vendor in seed.list_vendors()}
    rows = []
    for note in notes:
        short = sum(line.qty_ordered - line.qty_shipped for line in note.lines)
        status = (
            f'<span class="chip short">{short} short</span>'
            if short
            else '<span class="chip">Complete</span>'
        )
        rows.append(
            f'<tr><td><a href="/orders/{escape(note.po_id)}/delivery-note">'
            f"{escape(note.po_id)}</a></td>"
            f"<td>{escape(vendors.get(note.vendor_id, note.vendor_id))}</td>"
            f"<td>{escape(note.id)}</td>"
            f"<td>{escape(_fmt_date(note.ship_date))}</td>"
            f"<td>{status}</td></tr>"
        )
    empty_row = '<tr><td colspan="5">Nothing matches that search.</td></tr>'

    body = f"""
<h1>Orders</h1>
<p class="lede">{len(notes)} shipping document(s) available to
{escape(seed.COMPANY_NAME)}.</p>
<div class="card">
  <form class="search" method="get" action="/orders">
    <input type="text" name="q" placeholder="Search by order or item code"
      value="{escape(q or "")}">
    <button class="primary" type="submit">Search</button>
  </form>
  <table>
    <thead><tr><th>Order</th><th>Supplier</th><th>Delivery note</th><th>Shipped</th>
      <th>Status</th></tr></thead>
    <tbody>{"".join(rows) or empty_row}</tbody>
  </table>
</div>"""
    return HTMLResponse(_page("Orders", body, user))


@app.get("/orders/{po_id}/delivery-note", response_class=HTMLResponse)
def delivery_note(request: Request, po_id: str) -> Response:
    user = _current_user(request)
    if user is None:
        return _sign_in_redirect(request)

    note = seed.get_delivery_note(po_id)
    if note is None:
        body = (
            "<h1>Document not found</h1><p class='lede'>No delivery note has been published "
            f"for {escape(po_id)}.</p><div class='card'><a href='/orders'>Back to orders</a>"
            "</div>"
        )
        return HTMLResponse(_page("Not found", body, user), status_code=404)

    vendor = seed.get_vendor(note.vendor_id)
    vendor_name = vendor.name if vendor else note.vendor_id
    rows = []
    for line in note.lines:
        short = line.qty_ordered - line.qty_shipped
        flag = f'<span class="chip short">{short} short</span>' if short else ""
        rows.append(
            f"<tr><td>{line.line_no}</td><td>{escape(line.sku)}</td>"
            f"<td>{escape(line.description)} {flag}</td>"
            f"<td class='num'>{line.qty_ordered}</td>"
            f"<td class='num'><strong>{line.qty_shipped}</strong></td></tr>"
        )
    note_html = (
        f"<div class='note'><span>Note from supplier</span>{escape(note.note)}</div>"
        if note.note
        else ""
    )

    body = f"""
<h1>Delivery note {escape(note.id)}</h1>
<p class="lede">Published by {escape(vendor_name)} against order {escape(note.po_id)}.</p>
<div class="card">
  <div class="meta">
    <div><span>Order</span><strong>{escape(note.po_id)}</strong></div>
    <div><span>Ship date</span><strong>{escape(_fmt_date(note.ship_date))}</strong></div>
    <div><span>Carrier</span><strong>{escape(note.carrier)}</strong></div>
    <div><span>Tracking</span><strong>{escape(note.tracking)}</strong></div>
  </div>
  <table>
    <thead><tr><th>#</th><th>Item</th><th>Description</th><th class="num">Ordered</th>
      <th class="num">Shipped</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  {note_html}
</div>
<div class="card"><a href="/orders">Back to orders</a></div>"""
    return HTMLResponse(_page(f"Delivery note {note.id}", body, user))
