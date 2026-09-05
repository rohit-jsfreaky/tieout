"""Nine routes over the exception loop. No logic lives here.

    GET  /queue                        the exceptions, with where each one got to
    GET  /exceptions/{id}              the evidence pack and the proposed decision
    POST /exceptions/{id}/work         start an investigation on a thread
    GET  /exceptions/{id}/events       SSE: the engine's own events, live
    POST /exceptions/{id}/decide       record a human decision, return the rule it learned
    GET  /policies                     every rule, every version, and what it has cleared
    GET  /metrics                      human touches, auto-clears, evidence, citations
    POST /reset                        the world and Tieout's memory back to the seed
    GET  /screenshots/{name}           the PNG a portal Fact points at, as bytes

Each handler does the same three things: ask the engine, read the store, return the pydantic
object. If a line in this file ever compares a number to a threshold, cites a rule or opens a
browser, it belongs in ``engine/`` instead.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from ..engine import investigate, load_env, metrics, policy, store
from ..engine.events import Event
from ..engine.models import Decision, DecisionAction, ExceptionCase, Metrics, Policy
from ..engine.sources.portal import screenshot_dir
from . import runner
from .schemas import (
    DecideRequest,
    DecideResponse,
    ExceptionDetail,
    PoliciesResponse,
    PolicyRow,
    QueueResponse,
    QueueRow,
    ResetResponse,
    WorkAccepted,
)

# How long the stream waits on the queue before checking whether the client walked away.
POLL_SECONDS = 1.0
# A comment down the wire every this often, so proxies and browsers keep the stream open.
PING_SECONDS = 15


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Bring the fake company up if it is not already running, and put it down after."""
    load_env()
    await asyncio.to_thread(runner.ensure_world)
    yield
    await asyncio.to_thread(runner.stop_world)


app = FastAPI(
    title="Tieout",
    version="0.1.0",
    description="An agent that only works the invoices that broke.",
    lifespan=lifespan,
)

# A localhost demo: the desk runs on :3000, this runs on :8700, and there is no auth to leak.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------------------
# Reading the store — the same view the CLI prints, as JSON
# --------------------------------------------------------------------------------------


def _outcome(case: ExceptionCase) -> tuple[Decision | None, int]:
    """The decision that stands on this exception, and how much evidence is behind it.

    A recorded decision wins over the proposal on the pack: it is what actually happened.
    """
    pack = store.get_pack(case.id)
    decision = store.latest_decision(case.id) or (pack.proposal if pack else None)
    return decision, len(pack.facts) if pack else 0


def _cited_policy(decision: Decision | None) -> Policy | None:
    """Resolve ``SHORT-SHIP-01 v1`` back to the rule, so the desk can show the stamp."""
    if decision is None or not decision.cited_policy:
        return None
    policy_id, _, version = decision.cited_policy.partition(" v")
    return store.get_policy(policy_id, int(version) if version.isdigit() else None)


def _row(case: ExceptionCase) -> QueueRow:
    decision, facts = _outcome(case)
    return QueueRow(
        exception=case,
        decision=decision,
        facts=facts,
        running=runner.is_running(case.id),
    )


def _case_or_404(exception_id: str) -> ExceptionCase:
    case = runner.find(exception_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"no exception {exception_id}")
    return case


# --------------------------------------------------------------------------------------
# The routes
# --------------------------------------------------------------------------------------


@app.get("/queue", response_model=QueueResponse)
def queue() -> QueueResponse:
    """Three-way match every open invoice and return only the ones that broke."""
    cases = runner.refresh_queue()
    return QueueResponse(count=len(cases), exceptions=[_row(case) for case in cases])


@app.get("/exceptions/{exception_id}", response_model=ExceptionDetail)
def exception_detail(exception_id: str) -> ExceptionDetail:
    """The evidence pack and the decision — proposed, auto-cleared, refused or human."""
    case = _case_or_404(exception_id)
    pack = store.get_pack(case.id)
    decision = store.latest_decision(case.id) or (pack.proposal if pack else None)
    return ExceptionDetail(
        exception=case,
        pack=pack,
        decision=decision,
        policy=_cited_policy(decision),
        running=runner.is_running(case.id),
        events=f"/exceptions/{case.id}/events",
    )


@app.post("/exceptions/{exception_id}/work", response_model=WorkAccepted, status_code=202)
def work(exception_id: str, portal: bool = True) -> WorkAccepted:
    """Start the investigation on a thread. Watch ``/events`` to see it happen."""
    case = _case_or_404(exception_id)
    try:
        run = runner.start(case, use_portal=portal)
    except runner.Busy as busy:
        raise HTTPException(status_code=409, detail=str(busy)) from busy
    return WorkAccepted(
        exception_id=case.id,
        state=run.state.value,
        events=f"/exceptions/{case.id}/events",
    )


@app.get("/exceptions/{exception_id}/events")
async def events(request: Request, exception_id: str) -> EventSourceResponse:
    """The engine's events as they happen, forwarded verbatim.

    Every message is one ``engine.events.Event``, named by its own ``kind`` — ``step``,
    ``fact``, ``proposed``, ``auto_cleared``, ``policy_learned`` and the rest. The stream
    also sends one ``done`` message of its own when the run ends; that is transport, not
    evidence, and it is the only shape on this wire the engine did not write.
    """
    return EventSourceResponse(_stream(request, exception_id), ping=PING_SECONDS)


async def _stream(request: Request, exception_id: str) -> AsyncIterator[ServerSentEvent]:
    loop = asyncio.get_running_loop()
    run, replay, subscriber = runner.subscribe(exception_id, loop)
    try:
        for event in replay:
            yield _as_sse(event)
        if subscriber is None:
            yield _done(run)
            return
        while True:
            if await request.is_disconnected():
                return
            try:
                item = await asyncio.wait_for(subscriber.queue.get(), timeout=POLL_SECONDS)
            except TimeoutError:
                continue
            if item is None:
                break
            yield _as_sse(item)
        yield _done(runner.current(exception_id) or run)
    finally:
        if subscriber is not None:
            runner.unsubscribe(exception_id, subscriber)


def _as_sse(event: Event) -> ServerSentEvent:
    """One engine event, unchanged. The desk types against ``Event``, so nothing is reshaped."""
    return ServerSentEvent(event=event.kind.value, data=event.model_dump_json())


def _done(run: runner.Run) -> ServerSentEvent:
    payload: dict[str, Any] = {
        "exception_id": run.exception_id,
        "state": run.state.value,
        "error": run.error,
    }
    return ServerSentEvent(event="done", data=json.dumps(payload))


@app.post("/exceptions/{exception_id}/decide", response_model=DecideResponse)
def decide(exception_id: str, body: DecideRequest) -> DecideResponse:
    """Record what a person decided, and hand back the rule the engine learned from it."""
    case = _case_or_404(exception_id)
    try:
        decision, learned = investigate.apply_human_decision(
            case,
            action=DecisionAction(body.action),
            by=body.by,
            note=body.note,
            sink=lambda event: runner.emit(case.id, event),
        )
    except investigate.NotInvestigated as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return DecideResponse(
        exception=store.get_exception(case.id) or case,
        decision=decision,
        policy=learned,
    )


@app.get("/policies", response_model=PoliciesResponse)
def policies() -> PoliciesResponse:
    """Every rule and every version, with the exceptions each family has cleared."""
    rules = store.list_policies()
    return PoliciesResponse(
        count=len(rules),
        policies=[PolicyRow(policy=rule, cited_by=policy.citations(rule.id)) for rule in rules],
    )


@app.get("/metrics", response_model=Metrics)
def counters() -> Metrics:
    """Counted from the store on every request. Nothing here is typed in."""
    return metrics.compute()


@app.get("/screenshots/{name}", response_class=FileResponse)
def screenshot(name: str) -> FileResponse:
    """The PNG a portal ``Fact`` points at, so the desk can show what the browser saw.

    ``Fact.screenshot`` is an absolute path on the machine the engine ran on, which a browser
    cannot open. This hands back the same bytes over HTTP and nothing else: the name is
    reduced to its last component and has to land directly inside the screenshot folder, so
    no path a client sends can reach anything the engine did not write there.
    """
    root = screenshot_dir().resolve()
    path = (root / Path(name.replace("\\", "/")).name).resolve()
    if path.parent != root or not path.is_file():
        raise HTTPException(status_code=404, detail=f"no screenshot {name}")
    return FileResponse(path, media_type="image/png")


@app.post("/reset", response_model=ResetResponse)
def reset() -> ResetResponse:
    """The world, the store, the saved portal session and the screenshots — all back to zero."""
    try:
        world = runner.reset_everything()
    except runner.Busy as busy:
        raise HTTPException(status_code=409, detail=str(busy)) from busy
    return ResetResponse(
        message=(
            "The world is back to the seed and Tieout remembers nothing: "
            "no packs, no decisions, no policies, no session."
        ),
        world=world,
    )
