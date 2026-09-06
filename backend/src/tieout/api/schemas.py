"""What the API sends and accepts.

Every interesting shape is an engine model, re-exported unchanged: ``ExceptionCase``,
``EvidencePack``, ``Fact``, ``Decision``, ``Policy``, ``Metrics``. The wrappers below only
group them — they never add a field the engine could have computed, because the moment this
layer starts deriving numbers it has become a second, unauditable source of truth.

The SSE stream is not described here at all: it carries ``engine.events.Event`` verbatim.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..engine.models import Decision, EvidencePack, ExceptionCase, Policy, Role

# What a person is allowed to do with an exception. ``approve`` means "do what Tieout
# proposed"; the engine resolves it into the real action and records that on the trail.
DecidableAction = Literal["approve", "reject", "short_pay", "attach_po"]


class QueueRow(BaseModel):
    """One line of the desk's queue: the exception, and where it got to."""

    exception: ExceptionCase
    decision: Decision | None = None
    facts: int = 0
    running: bool = False


class QueueResponse(BaseModel):
    count: int
    exceptions: list[QueueRow] = Field(default_factory=list)


class ExceptionDetail(BaseModel):
    """The evidence pack and the proposed decision — or the refusal, which is also a decision."""

    exception: ExceptionCase
    pack: EvidencePack | None = None
    decision: Decision | None = None
    policy: Policy | None = None
    running: bool = False
    events: str


class WorkAccepted(BaseModel):
    """202: the investigation is running on a thread. Watch ``events`` to see it happen."""

    exception_id: str
    state: str
    events: str


class DecideRequest(BaseModel):
    action: DecidableAction
    by: str = Field(min_length=1, description='who decided, e.g. "Chris, Controller"')
    #: Their seat in the delegation-of-authority matrix. Left out, it is read off ``by`` when
    #: that is written ``"Name, Role"`` — which is how the CLI has always spelled it.
    role: Role | None = None
    note: str = ""


class DecideResponse(BaseModel):
    """The decision, the exception's new status, and the rule that came out of it."""

    exception: ExceptionCase
    decision: Decision
    policy: Policy | None = None


class AuthorityRow(BaseModel):
    """One seat in the delegation-of-authority matrix. ``limit: null`` means no limit."""

    role: Role
    limit: float | None = None


class AuthorityResponse(BaseModel):
    """The matrix itself, so a client can label a role without inventing a number."""

    matrix: list[AuthorityRow] = Field(default_factory=list)
    note: str


class PolicyRow(BaseModel):
    policy: Policy
    cited_by: list[str] = Field(default_factory=list)


class PoliciesResponse(BaseModel):
    count: int
    policies: list[PolicyRow] = Field(default_factory=list)


class ResetResponse(BaseModel):
    message: str
    world: dict[str, Any] = Field(default_factory=dict)
