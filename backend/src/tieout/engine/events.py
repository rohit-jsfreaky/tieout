"""Typed events. The engine never prints — it emits.

The CLI renders these as lines; Phase 3 fans the same objects out over SSE, so the desk
watches an investigation happen live without the engine knowing a screen exists.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .models import Decision, Fact, LookupStep, Policy


class EventKind(StrEnum):
    MATCHED = "matched"
    INVESTIGATING = "investigating"
    STEP = "step"
    FACT = "fact"
    ENOUGH = "enough"
    PROPOSED = "proposed"
    REFUSED = "refused"
    AUTO_CLEARED = "auto_cleared"
    DECIDED = "decided"
    POLICY_LEARNED = "policy_learned"
    POLICY_VERSIONED = "policy_versioned"
    WARNING = "warning"


class Event(BaseModel):
    kind: EventKind
    message: str
    at: datetime = Field(default_factory=datetime.now)
    exception_id: str | None = None
    fact: Fact | None = None
    step: LookupStep | None = None
    decision: Decision | None = None
    policy: Policy | None = None


EventSink = Callable[[Event], None]


def null_sink(event: Event) -> None:
    """The default: emit into nowhere. A library that prints is a library you cannot host."""
