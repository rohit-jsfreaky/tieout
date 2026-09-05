"""Every shape the engine passes across a file boundary.

Naming note: the exception a controller cares about is an ``ExceptionCase``, not
``Exception`` — shadowing the builtin in a module imported by every other file is the kind
of clever that costs an hour at 3am.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

# --------------------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------------------


class Source(StrEnum):
    """The three places Tieout is allowed to look."""

    ERP = "erp"
    INBOX = "inbox"
    PORTAL = "portal"


class FactKind(StrEnum):
    """What a Fact is about. The decision checklists are written in these terms."""

    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    GOODS_RECEIPT = "goods_receipt"
    CANDIDATE_PO = "candidate_purchase_order"
    VENDOR_EMAIL = "vendor_email"
    DELIVERY_NOTE = "delivery_note"
    PORTAL_ABSENCE = "portal_absence"


class ExceptionKind(StrEnum):
    SHORT_SHIP = "short_ship"
    PRICE_VARIANCE = "price_variance"
    MISSING_PO = "missing_po"
    UNKNOWN = "unknown"


class DecisionAction(StrEnum):
    SHORT_PAY = "short_pay"
    APPROVE = "approve"
    ATTACH_PO = "attach_po"
    REJECT = "reject"
    REFUSE = "refuse"


class ExceptionStatus(StrEnum):
    OPEN = "open"
    PROPOSED = "proposed"
    REFUSED = "refused"
    AUTO_CLEARED = "auto_cleared"
    RESOLVED = "resolved"


# --------------------------------------------------------------------------------------
# The exception
# --------------------------------------------------------------------------------------


class LineDiscrepancy(BaseModel):
    """One invoice line, next to what the order said and what the dock actually received."""

    line_no: int
    sku: str
    description: str
    qty_billed: int
    qty_received: int | None = None
    qty_ordered: int | None = None
    unit_price_billed: float
    unit_price_ordered: float | None = None

    @computed_field
    @property
    def qty_short(self) -> int:
        if self.qty_received is None:
            return 0
        return max(self.qty_billed - self.qty_received, 0)

    @computed_field
    @property
    def price_delta(self) -> float:
        if self.unit_price_ordered is None:
            return 0.0
        return round(self.unit_price_billed - self.unit_price_ordered, 2)

    @computed_field
    @property
    def price_delta_pct(self) -> float:
        if not self.unit_price_ordered:
            return 0.0
        return round(self.price_delta / self.unit_price_ordered * 100, 2)

    @computed_field
    @property
    def overbilled(self) -> float:
        """Money on this line that the receipt and the order do not support."""
        supported_qty = self.qty_billed if self.qty_received is None else self.qty_received
        supported_price = self.unit_price_ordered or self.unit_price_billed
        return round(self.qty_billed * self.unit_price_billed - supported_qty * supported_price, 2)


class ExceptionCase(BaseModel):
    """An invoice that did not tie out, and the numbers that prove it."""

    id: str
    invoice_id: str
    vendor_id: str
    vendor_name: str
    po_id: str | None
    kind: ExceptionKind
    headline: str
    amount: float
    currency: str
    invoice_date: date
    detected_at: datetime
    status: ExceptionStatus = ExceptionStatus.OPEN
    lines: list[LineDiscrepancy] = Field(default_factory=list)

    @computed_field
    @property
    def qty_billed(self) -> int:
        return sum(line.qty_billed for line in self.lines)

    @computed_field
    @property
    def qty_received(self) -> int:
        return sum(line.qty_received or 0 for line in self.lines)

    @computed_field
    @property
    def qty_short(self) -> int:
        return sum(line.qty_short for line in self.lines)

    @computed_field
    @property
    def short_pct(self) -> float:
        """How much of the billed quantity never arrived, as a percentage."""
        billed = self.qty_billed
        return round(self.qty_short / billed * 100, 2) if billed else 0.0

    @computed_field
    @property
    def price_variance_pct(self) -> float:
        """The worst per-unit price variance on the invoice."""
        return max((line.price_delta_pct for line in self.lines), default=0.0)

    @computed_field
    @property
    def exposure(self) -> float:
        """The money at stake: billed, minus what the order and the receipt support."""
        return round(sum(line.overbilled for line in self.lines), 2)

    @computed_field
    @property
    def supported_amount(self) -> float:
        """What Tieout believes is genuinely payable."""
        return round(self.amount - self.exposure, 2)


# --------------------------------------------------------------------------------------
# The audit trail
# --------------------------------------------------------------------------------------


class Figures(BaseModel):
    """Numbers a Fact carries, so a later check is arithmetic and not string matching."""

    qty_ordered: int | None = None
    qty_shipped: int | None = None
    qty_received: int | None = None
    qty_billed: int | None = None
    unit_price: float | None = None
    amount: float | None = None
    event_date: date | None = None


class Fact(BaseModel):
    """Something Tieout observed. Written only by ``evidence.py``."""

    id: str
    exception_id: str
    source: Source
    kind: FactKind
    statement: str
    locator: str
    observed_at: datetime
    raw: str
    figures: Figures = Field(default_factory=Figures)
    screenshot: str | None = None
    extracted_by: str = "code"


class LookupStep(BaseModel):
    """Somewhere Tieout looked, including the places that held nothing.

    A dead end is evidence too: it is most of why the engine refuses E5 instead of guessing.
    """

    source: Source
    action: str
    locator: str
    found: bool
    at: datetime
    note: str = ""


class Check(BaseModel):
    """One line of a class's deterministic checklist. The checklist IS the confidence."""

    name: str
    passed: bool
    weight: float
    detail: str


class Decision(BaseModel):
    """What Tieout proposes, or what actually happened. Never written by the model."""

    exception_id: str
    action: DecisionAction
    summary: str
    rationale: str
    rationale_by: str = "code"
    confidence: float
    checks: list[Check] = Field(default_factory=list)
    auto: bool = False
    cited_policy: str | None = None
    approved_by: str | None = None
    decided_at: datetime
    amount_payable: float | None = None
    attach_po: str | None = None
    note: str = ""


class EvidencePack(BaseModel):
    """Everything Tieout found on one exception, and what it wants to do about it."""

    exception: ExceptionCase
    facts: list[Fact] = Field(default_factory=list)
    steps: list[LookupStep] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime | None = None
    proposal: Decision | None = None

    @computed_field
    @property
    def sources_used(self) -> list[Source]:
        seen: list[Source] = []
        for step in self.steps:
            if step.source not in seen:
                seen.append(step.source)
        return seen

    def facts_of(self, kind: FactKind) -> list[Fact]:
        return [fact for fact in self.facts if fact.kind == kind]

    def has(self, kind: FactKind) -> bool:
        return any(fact.kind == kind for fact in self.facts)


# --------------------------------------------------------------------------------------
# The rule
# --------------------------------------------------------------------------------------


class PolicyCondition(BaseModel):
    """A rule's "when". Every field is evaluated by code in ``policy.py``, never by a model.

    ``None`` means this dimension is not constrained.
    """

    kind: ExceptionKind
    vendor_id: str | None = None
    vendor_name: str | None = None
    max_short_pct: float | None = None
    max_price_variance_pct: float | None = None
    max_exposure: float | None = None
    requires: list[FactKind] = Field(default_factory=list)

    def describe(self) -> str:
        parts = [f"class is {self.kind.value}"]
        if self.vendor_id:
            parts.append(f"vendor is {self.vendor_name or self.vendor_id}")
        if self.max_short_pct is not None:
            parts.append(f"shortfall <= {self.max_short_pct:g}% of the billed quantity")
        if self.max_price_variance_pct is not None:
            parts.append(f"price variance <= {self.max_price_variance_pct:g}%")
        if self.max_exposure is not None:
            parts.append(f"exposure <= {self.max_exposure:,.2f}")
        if self.requires:
            parts.append("evidence includes " + ", ".join(k.value for k in self.requires))
        return "; ".join(parts)


class Policy(BaseModel):
    """A rule Tieout learned from one human decision, with that human's name on it."""

    id: str
    version: int
    name: str
    kind: ExceptionKind
    condition: PolicyCondition
    action: DecisionAction
    rationale: str
    drafted_by: str = "code"
    approved_by: str
    approved_at: datetime
    learned_from: str
    learned_from_invoice: str
    active: bool = True
    superseded_at: datetime | None = None
    supersedes_version: int | None = None

    @computed_field
    @property
    def ref(self) -> str:
        return f"{self.id} v{self.version}"


class Metrics(BaseModel):
    """Counted from the store. Nothing here is hard-coded."""

    exceptions_found: int = 0
    worked: int = 0
    auto_cleared: int = 0
    refused: int = 0
    awaiting_human: int = 0
    human_touches: int = 0
    touches_avoided_by_policy: int = 0
    evidence_items: int = 0
    screenshots: int = 0
    policies_active: int = 0
    policy_citations: int = 0
