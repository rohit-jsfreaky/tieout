"""The ONLY writer of the audit trail. A Fact that did not come through here does not exist.

Every Fact carries where it came from (``source``), exactly how to fetch it again
(``locator``), when it was seen (``observed_at``), the raw material it was read from
(``raw``), and — for anything read off the vendor portal — a screenshot that is on disk.

The trail also records the places Tieout looked and found nothing. Those dead ends are why
the refusal in beat four is a considered answer rather than a shrug.

Three rules are enforced here, not politely requested:

* a portal Fact without a real screenshot file is rejected;
* a Fact dated outside the open fiscal window is rejected (the model guessed "2024" on the
  very first test call — a silently wrong year is exactly the bad evidence that must never
  reach a human);
* an empty statement, locator or raw is rejected.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from .events import Event, EventKind, EventSink, null_sink
from .models import (
    Decision,
    EvidencePack,
    ExceptionCase,
    Fact,
    FactKind,
    Figures,
    LookupStep,
    Source,
)

# How far either side of the world's period start a date may fall and still be believable.
WINDOW_BEFORE_DAYS = 45
WINDOW_AFTER_DAYS = 75


class EvidenceError(RuntimeError):
    """Evidence that would not survive an audit. Refused at the door."""


class EvidenceTrail:
    """One exception's trail, being written. ``pack()`` seals it."""

    def __init__(
        self,
        case: ExceptionCase,
        *,
        period_start: date,
        sink: EventSink = null_sink,
    ) -> None:
        self.case = case
        self.period_start = period_start
        self.window_start = period_start - timedelta(days=WINDOW_BEFORE_DAYS)
        self.window_end = period_start + timedelta(days=WINDOW_AFTER_DAYS)
        self.started_at = datetime.now()
        self._sink = sink
        self._facts: list[Fact] = []
        self._steps: list[LookupStep] = []

    # -- writing ------------------------------------------------------------------------

    def looked(
        self,
        *,
        source: Source,
        action: str,
        locator: str,
        found: bool,
        note: str = "",
    ) -> LookupStep:
        """Record that Tieout looked somewhere. ``found=False`` is the interesting case."""
        step = LookupStep(
            source=source,
            action=action.strip(),
            locator=locator.strip(),
            found=found,
            at=datetime.now(),
            note=note.strip(),
        )
        self._steps.append(step)
        self._sink(
            Event(
                kind=EventKind.STEP,
                exception_id=self.case.id,
                message=step.action,
                step=step,
            )
        )
        return step

    def record(
        self,
        *,
        source: Source,
        kind: FactKind,
        statement: str,
        locator: str,
        raw: str,
        figures: Figures | None = None,
        screenshot: str | Path | None = None,
        extracted_by: str = "code",
    ) -> Fact:
        """Put one observation on the trail, or refuse it and say why."""
        figures = figures or Figures()
        if not statement.strip():
            raise EvidenceError("a fact with no statement is not a fact")
        if not locator.strip():
            raise EvidenceError(f"no locator for {statement!r}: nobody could check it")
        if not raw.strip():
            raise EvidenceError(f"no raw material behind {statement!r}")

        shot = str(screenshot) if screenshot else None
        if source is Source.PORTAL:
            if shot is None:
                raise EvidenceError("a portal fact needs a screenshot")
            if not Path(shot).is_file():
                raise EvidenceError(f"the screenshot for {statement!r} is not on disk: {shot}")

        self._check_window(figures.event_date, statement)

        fact = Fact(
            id=f"{self.case.id}-F{len(self._facts) + 1:02d}",
            exception_id=self.case.id,
            source=source,
            kind=kind,
            statement=statement.strip(),
            locator=locator.strip(),
            observed_at=datetime.now(),
            raw=raw.strip(),
            figures=figures,
            screenshot=shot,
            extracted_by=extracted_by,
        )
        self._facts.append(fact)
        self._sink(
            Event(
                kind=EventKind.FACT,
                exception_id=self.case.id,
                message=fact.statement,
                fact=fact,
            )
        )
        return fact

    def _check_window(self, when: date | None, statement: str) -> None:
        if when is None:
            return
        if not (self.window_start <= when <= self.window_end):
            raise EvidenceError(
                f"{statement!r} is dated {when.isoformat()}, outside the open period "
                f"({self.window_start.isoformat()} to {self.window_end.isoformat()})"
            )

    def warn(self, message: str) -> None:
        """Something the trail should say out loud but that is not itself evidence."""
        self._sink(Event(kind=EventKind.WARNING, exception_id=self.case.id, message=message))

    # -- reading ------------------------------------------------------------------------

    @property
    def facts(self) -> list[Fact]:
        return list(self._facts)

    @property
    def steps(self) -> list[LookupStep]:
        return list(self._steps)

    def facts_of(self, kind: FactKind) -> list[Fact]:
        return [fact for fact in self._facts if fact.kind == kind]

    def has(self, kind: FactKind) -> bool:
        return any(fact.kind == kind for fact in self._facts)

    def pack(self, proposal: Decision | None = None) -> EvidencePack:
        """Seal the trail into the pack a human (or the desk) reads."""
        return EvidencePack(
            exception=self.case,
            facts=self.facts,
            steps=self.steps,
            started_at=self.started_at,
            finished_at=datetime.now(),
            proposal=proposal,
        )
