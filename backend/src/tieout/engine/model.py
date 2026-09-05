"""The ONLY file in Tieout that calls a language model. Three named jobs, nothing else.

    1. ``facts_from_text``      unstructured vendor email  -> Facts a controller could check
    2. ``draft_rationale``      a decision the code made   -> the paragraph that explains it
    3. ``generalise_decision``  one human decision         -> a DRAFT rule, for code to clamp

What the model never does: apply a rule, compute a confidence, or decide anything. Those are
deterministic code, which is what makes "auto-cleared citing SHORT-SHIP-01, approved by
Chris" reproducible when a judge reruns it.

Provider is any OpenAI-compatible endpoint (TensorMux during the hackathon, OpenRouter as the
backup): base URL, key and model id come from the environment.

Three hard-won facts about the model we are actually running, verified 2026-09-05
(see ``RESEARCH.md`` -> "Model provider"):

* ``glm-4-7-flash`` is a REASONING model. It fills a separate ``reasoning`` field first and
  leaves ``content`` EMPTY until it is done. That arrives as HTTP 200 with a blank answer.
  Empty content is therefore a FAILURE here, never an answer, and never a Fact.
* It wraps JSON in a markdown fence. Strip the fence before ``json.loads``.
* It invents the year unless the prompt states today's date. Every prompt states it.
"""

from __future__ import annotations

import json
import os
import time
from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from . import load_env
from .models import Check, ExceptionCase, Fact, Figures

# --------------------------------------------------------------------------------------
# Configuration — pinned constants at the top, values from the environment
# --------------------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://api.tensormux.com/v1"
DEFAULT_MODEL_ID = "glm-4-7-flash"
DEFAULT_MAX_TOKENS = 800
MIN_MAX_TOKENS = 600  # below this the reasoning field eats the whole budget and content is ""
TEMPERATURE = 0.0
TIMEOUT_SECONDS = 120.0
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 5.0
RETRY_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504})

# Ask the reasoning model to answer instead of thinking out loud. vLLM passes this through to
# the chat template; a provider that does not understand it ignores it, which is why the
# token escalation below still exists. Measured 2026-09-05: 2.9s and 150 completion tokens
# with this, against 19.7s and 1,912 without.
NO_THINKING = {"chat_template_kwargs": {"enable_thinking": False}}

# If it thinks anyway, the whole budget goes into `reasoning` and `content` comes back empty.
# That is a retryable failure, and the retry is worth more room rather than more patience.
TOKEN_ESCALATION = 2


class ModelError(RuntimeError):
    """The model did not answer. Callers degrade; they never invent the answer."""


def base_url() -> str:
    load_env()
    return (os.environ.get("MODEL_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def model_id() -> str:
    load_env()
    return os.environ.get("MODEL_ID") or DEFAULT_MODEL_ID


def max_tokens() -> int:
    load_env()
    raw = os.environ.get("MODEL_MAX_TOKENS")
    wanted = int(raw) if raw and raw.isdigit() else DEFAULT_MAX_TOKENS
    return max(wanted, MIN_MAX_TOKENS)


def available() -> bool:
    """No key, no calls. The engine still runs — it just writes its own prose."""
    load_env()
    return bool(os.environ.get("MODEL_API_KEY"))


def label() -> str:
    """What goes on a Fact's ``extracted_by``, so the trail says who wrote each sentence."""
    return f"model:{model_id()}"


# --------------------------------------------------------------------------------------
# The one HTTP call
# --------------------------------------------------------------------------------------


def _strip_fence(text: str) -> str:
    """``` ```json {...} ``` ``` -> ``{...}``. The model fences its JSON every single time."""
    body = text.strip()
    if not body.startswith("```"):
        return body
    lines = body.splitlines()
    lines = lines[1:]
    while lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()


def _chat(system: str, user: str) -> str:
    """One completion. Returns non-empty content or raises."""
    if not available():
        raise ModelError("MODEL_API_KEY is not set")

    payload: dict[str, Any] = {
        "model": model_id(),
        "temperature": TEMPERATURE,
        "max_tokens": max_tokens(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **NO_THINKING,
    }
    headers = {"Authorization": f"Bearer {os.environ['MODEL_API_KEY']}"}
    url = f"{base_url()}/chat/completions"

    last_error = "no attempt was made"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait = BACKOFF_SECONDS * attempt
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
        except httpx.HTTPError as exc:
            last_error = f"transport error: {exc}"
        else:
            if response.status_code in RETRY_STATUS:
                last_error = f"HTTP {response.status_code}"
            elif response.status_code >= 400:
                raise ModelError(f"HTTP {response.status_code}: {response.text[:200]}")
            else:
                # The `reasoning` field is the model thinking out loud. It is never evidence,
                # it is never stored, and a reply that has only reasoning is a failed call.
                message = response.json()["choices"][0]["message"]
                content = (message.get("content") or "").strip()
                if content:
                    return content
                last_error = "the model returned reasoning but no answer"
                # It thought instead of answering. Give it room rather than time.
                payload["max_tokens"] *= TOKEN_ESCALATION
                wait = 0.0
        if attempt < MAX_ATTEMPTS and wait:
            time.sleep(wait)
    raise ModelError(f"{model_id()} did not answer after {MAX_ATTEMPTS} attempts: {last_error}")


def _chat_json(system: str, user: str) -> dict[str, Any]:
    raw = _strip_fence(_chat(system + "\n\nAnswer with JSON only. No prose, no fence.", user))
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelError(f"the model did not return JSON: {raw[:200]}") from exc
    if not isinstance(parsed, dict):
        raise ModelError(f"expected a JSON object, got {type(parsed).__name__}")
    return parsed


def _dateline(today: date) -> str:
    """Every prompt carries the real date. Without it the model invents the year."""
    return (
        f"Today is {today:%Y-%m-%d} ({today:%d %B %Y}). Any date you output must use this "
        "year unless the text you are reading states a different one explicitly."
    )


# --------------------------------------------------------------------------------------
# Job 1 — facts from unstructured text
# --------------------------------------------------------------------------------------


class ExtractedFact(BaseModel):
    statement: str
    figures: Figures = Field(default_factory=Figures)


class _ExtractionReply(BaseModel):
    facts: list[ExtractedFact] = Field(default_factory=list)


FACTS_SYSTEM = (
    "You are an accounts payable analyst reading vendor correspondence. You extract only "
    "what the text actually says. You never guess, never infer a number that is not written, "
    "and never repeat the same claim twice. Each statement is one short sentence in the past "
    "tense, naming who said it, so a controller can check it against the document."
)

FACTS_SCHEMA = """Return this shape:
{"facts": [{"statement": "...",
            "figures": {"qty_ordered": null, "qty_shipped": null, "qty_received": null,
                        "qty_billed": null, "unit_price": null, "amount": null,
                        "event_date": "YYYY-MM-DD or null"}}]}
Use null for anything the text does not state. Return at most 3 facts."""


def facts_from_text(
    text: str, *, subject: str, sender: str, context: str, today: date
) -> list[ExtractedFact]:
    """Job 1. Turn an email body into checkable claims. Raises ModelError if it cannot."""
    user = (
        f"{_dateline(today)}\n\n"
        f"Context: {context}\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f'Body:\n"""\n{text.strip()}\n"""\n\n'
        f"{FACTS_SCHEMA}"
    )
    try:
        reply = _ExtractionReply.model_validate(_chat_json(FACTS_SYSTEM, user))
    except ValidationError as exc:
        raise ModelError(f"extraction did not match the schema: {exc}") from exc
    return [fact for fact in reply.facts if fact.statement.strip()]


# --------------------------------------------------------------------------------------
# Job 2 — the rationale for a decision the code has already made
# --------------------------------------------------------------------------------------

# The exception is a finding, not a claim to be adjudicated. Left to itself the model wrote
# "Exception E4 is invalid because the supplier confirmed there is no order number", which is
# backwards: the supplier confirming it is exactly what makes the exception real. Naming that
# failure in the prompt is cheaper and more honest than filtering the prose afterwards.
RATIONALE_SYSTEM = (
    "You are Tieout, an accounts payable agent writing the one-paragraph justification that "
    "goes on an audit trail. The decision and the numbers are already fixed and you must not "
    "change them. The exception itself is already established: a deterministic three-way "
    "match raised it, so it is a confirmed finding and never a claim for you to judge. Never "
    "call the exception valid, invalid, unfounded or a false positive, and never open with a "
    "verdict on it. Evidence that agrees with the exception CONFIRMS it. Write four sentences "
    "at most, in this order: what did not tie out, what the evidence shows and which source "
    "it came from, and why the proposed action follows from that evidence. Plain English, no "
    "bullet points, no headings, no invented facts."
)


def draft_rationale(
    case: ExceptionCase,
    facts: list[Fact],
    checks: list[Check],
    *,
    action: str,
    proposal: str,
    today: date,
) -> str:
    """Job 2. Prose only — the action, the amount and the confidence are already decided."""
    evidence = "\n".join(f"- [{fact.source.value}] {fact.statement}" for fact in facts) or "- none"
    checklist = "\n".join(
        f"- {check.name}: {'pass' if check.passed else 'FAIL'} — {check.detail}" for check in checks
    )
    user = (
        f"{_dateline(today)}\n\n"
        f"Confirmed exception {case.id} on invoice {case.invoice_id} from {case.vendor_name}.\n"
        f"What did not tie out - class {case.kind.value}: {case.headline}\n"
        f"Invoice total {case.amount:,.2f} {case.currency}; "
        f"unsupported amount {case.exposure:,.2f} {case.currency}.\n\n"
        f"Evidence on the trail:\n{evidence}\n\n"
        f"Deterministic checklist:\n{checklist}\n\n"
        f"Proposed action: {action} — {proposal}\n\n"
        "Write the justification paragraph."
    )
    return _chat(RATIONALE_SYSTEM, user).strip()


# --------------------------------------------------------------------------------------
# Job 3 — generalise one human decision into a DRAFT rule
# --------------------------------------------------------------------------------------


class RuleDraft(BaseModel):
    """What the model suggests. ``policy.py`` clamps every number before anything is stored."""

    name: str
    scope: str = "vendor"  # "vendor" or "any"
    tolerance_pct: float = 0.0
    rationale: str = ""


RULE_SYSTEM = (
    "You are Tieout, an accounts payable agent turning one approved decision into a reusable "
    "policy so the same kind of exception never needs a human again. Be conservative: a rule "
    "that is too wide pays money nobody approved. Name the rule in plain English, under ten "
    "words. The tolerance is a percentage and must never be more than double what this case "
    "showed. Scope is 'vendor' when the reasoning depends on how this supplier behaves, and "
    "'any' only when it would obviously hold for every supplier."
)

RULE_SCHEMA = """Return this shape:
{"name": "...", "scope": "vendor" | "any", "tolerance_pct": 0.0, "rationale": "one sentence"}"""


def generalise_decision(
    case: ExceptionCase,
    *,
    action: str,
    approved_by: str,
    observed_variance_pct: float,
    today: date,
) -> RuleDraft:
    """Job 3. A DRAFT only. The stored condition is built and bounded by ``policy.py``."""
    user = (
        f"{_dateline(today)}\n\n"
        f"{approved_by} approved this decision:\n"
        f"- Exception {case.id}, invoice {case.invoice_id}, supplier {case.vendor_name}.\n"
        f"- Class: {case.kind.value}. {case.headline}\n"
        f"- The variance in this case was {observed_variance_pct:.2f}%.\n"
        f"- Amount at stake: {case.exposure:,.2f} {case.currency} of "
        f"{case.amount:,.2f} {case.currency}.\n"
        f"- Action taken: {action}.\n\n"
        f"{RULE_SCHEMA}"
    )
    try:
        return RuleDraft.model_validate(_chat_json(RULE_SYSTEM, user))
    except ValidationError as exc:
        raise ModelError(f"rule draft did not match the schema: {exc}") from exc
