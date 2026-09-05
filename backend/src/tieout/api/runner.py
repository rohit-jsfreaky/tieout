"""Runs an investigation on a thread and puts the engine's events on a wire.

Nothing here judges anything. It calls ``engine.investigate.work``, keeps that run's
``Event`` objects in the order the engine emitted them, and hands each one to every open SSE
stream **unchanged**. The desk types against ``engine.events.Event``; this file must never
invent a shape of its own.

Two things it does own, because they are process plumbing rather than product:

* **One investigation at a time.** The browser, the saved VendorLink session and the
  screenshot folder are a single shared resource, so a second ``/work`` while one is running
  is a 409 rather than a race.
* **The world.** The API is useless without the ERP, the portal and the mailbox, so it starts
  them in-process if nobody else has — exactly as ``tieout demo`` does.
"""

from __future__ import annotations

import asyncio
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import httpx

from ..engine import investigate, match, store
from ..engine.events import Event
from ..engine.models import ExceptionCase
from ..engine.sources.erp import ErpClient
from ..engine.sources.erp import default_base_url as erp_url
from ..engine.sources.inbox import InboxClient
from ..engine.sources.portal import default_base_url as portal_url
from ..engine.sources.portal import forget_session, screenshot_dir
from ..world import __main__ as world_main

HEALTH_TIMEOUT_SECONDS = 2.0


class RunState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Busy(RuntimeError):
    """Something is already using the browser. Wait for it rather than fight it."""


@dataclass
class Subscriber:
    """One open SSE stream: its event loop, and the queue this thread pushes into."""

    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[Event | None]


@dataclass
class Run:
    """One exception's event history, and whoever is currently watching it."""

    exception_id: str
    state: RunState = RunState.IDLE
    events: list[Event] = field(default_factory=list)
    error: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    subscribers: list[Subscriber] = field(default_factory=list)


_RUNS: dict[str, Run] = {}
_LOCK = threading.RLock()

_WORLD: world_main.Running | None = None
_WORLD_LOCK = threading.Lock()


# --------------------------------------------------------------------------------------
# The world
# --------------------------------------------------------------------------------------


def world_is_up() -> bool:
    try:
        return httpx.get(f"{erp_url()}/health", timeout=HEALTH_TIMEOUT_SECONDS).status_code == 200
    except httpx.HTTPError:
        return False


def ensure_world() -> bool:
    """Start the fake company unless it is already running. True if this process started it."""
    global _WORLD
    with _WORLD_LOCK:
        if _WORLD is not None or world_is_up():
            return False
        _WORLD = world_main.start_background()
        return True


def stop_world() -> None:
    """Only stops what this process started. A world someone else runs is left alone."""
    global _WORLD
    with _WORLD_LOCK:
        if _WORLD is not None:
            _WORLD.stop()
            _WORLD = None


# --------------------------------------------------------------------------------------
# The queue
# --------------------------------------------------------------------------------------


def refresh_queue() -> list[ExceptionCase]:
    """Re-run the three-way match and persist it. Deterministic, and never reads the seed."""
    ensure_world()
    with ErpClient() as erp:
        cases = match.run(erp)
    store.save_exceptions(cases)
    return store.list_exceptions()


def find(exception_id: str) -> ExceptionCase | None:
    """An exception by id or invoice number, matching first if the store is cold."""
    case = store.get_exception(exception_id)
    if case is not None:
        return case
    refresh_queue()
    return store.get_exception(exception_id)


def reset_everything() -> dict[str, Any]:
    """The world back to the seed, and Tieout back to knowing nothing at all."""
    occupied = busy_with()
    if occupied is not None:
        raise Busy(f"an investigation is running on {occupied}")
    path = world_main.seed.reset_world()
    store.reset()
    forget_session()
    shutil.rmtree(screenshot_dir(), ignore_errors=True)
    _forget_runs()
    return world_main.seed.summary(path)


# --------------------------------------------------------------------------------------
# Runs
# --------------------------------------------------------------------------------------


def _run_for(exception_id: str) -> Run:
    """Caller holds ``_LOCK``."""
    run = _RUNS.get(exception_id)
    if run is None:
        run = Run(exception_id=exception_id)
        _RUNS[exception_id] = run
    return run


def current(exception_id: str) -> Run | None:
    with _LOCK:
        return _RUNS.get(exception_id)


def is_running(exception_id: str) -> bool:
    run = current(exception_id)
    return run is not None and run.state is RunState.RUNNING


def busy_with() -> str | None:
    """The exception currently holding the browser, if any."""
    with _LOCK:
        return next(
            (run.exception_id for run in _RUNS.values() if run.state is RunState.RUNNING), None
        )


def _forget_runs() -> None:
    """Empty every buffer without dropping anyone already watching a stream."""
    with _LOCK:
        for run in _RUNS.values():
            run.events = []
            run.state = RunState.IDLE
            run.error = ""
            run.started_at = None
            run.finished_at = None


def start(case: ExceptionCase, *, use_portal: bool = True) -> Run:
    """Investigate one exception on a worker thread. Raises ``Busy`` if one is already going."""
    with _LOCK:
        occupied = busy_with()
        if occupied is not None:
            raise Busy(f"an investigation is already running on {occupied}")
        run = _run_for(case.id)
        run.state = RunState.RUNNING
        run.events = []
        run.error = ""
        run.started_at = datetime.now()
        run.finished_at = None

    threading.Thread(
        target=_work,
        args=(run, case, use_portal),
        name=f"tieout-work-{case.id}",
        daemon=True,
    ).start()
    return run


def _work(run: Run, case: ExceptionCase, use_portal: bool) -> None:
    try:
        ensure_world()
        with ErpClient() as erp, InboxClient() as inbox:
            sources = investigate.Sources(
                erp=erp,
                inbox=inbox,
                portal_base_url=portal_url(),
                use_portal=use_portal,
            )
            investigate.work(case, sources, sink=lambda event: emit(case.id, event))
    except Exception as exc:  # a worker thread that dies quietly is a stream that hangs
        _finish(run, RunState.FAILED, f"{type(exc).__name__}: {exc}")
    else:
        _finish(run, RunState.DONE, "")


def _finish(run: Run, state: RunState, error: str) -> None:
    with _LOCK:
        run.state = state
        run.error = error
        run.finished_at = datetime.now()
        watching, run.subscribers = list(run.subscribers), []
    for subscriber in watching:
        _push(subscriber, None)


# --------------------------------------------------------------------------------------
# Fan-out — the engine's events, unchanged
# --------------------------------------------------------------------------------------


def emit(exception_id: str, event: Event) -> None:
    """The ``EventSink`` the engine is handed. Buffer it, then wake every open stream."""
    with _LOCK:
        run = _run_for(exception_id)
        run.events.append(event)
        watching = list(run.subscribers)
    for subscriber in watching:
        _push(subscriber, event)


def _push(subscriber: Subscriber, item: Event | None) -> None:
    try:
        subscriber.loop.call_soon_threadsafe(subscriber.queue.put_nowait, item)
    except RuntimeError:
        pass  # the client's loop has gone: that stream is already closed


def subscribe(
    exception_id: str, loop: asyncio.AbstractEventLoop
) -> tuple[Run, list[Event], Subscriber | None]:
    """Everything that has happened, plus a seat for whatever happens next.

    Both halves are taken under one lock, so a stream can neither miss an event nor see one
    twice. A subscriber of ``None`` means the run is already over: replay it and close.
    """
    subscriber = Subscriber(loop=loop, queue=asyncio.Queue())
    with _LOCK:
        run = _run_for(exception_id)
        replay = list(run.events)
        if run.state in {RunState.DONE, RunState.FAILED}:
            return run, replay, None
        run.subscribers.append(subscriber)
    return run, replay, subscriber


def unsubscribe(exception_id: str, subscriber: Subscriber) -> None:
    with _LOCK:
        run = _RUNS.get(exception_id)
        if run is not None and subscriber in run.subscribers:
            run.subscribers.remove(subscriber)
