"""Phase 3: the four beats over HTTP, with the stream open.

These tests drive the real app against the real test world — including a real Chromium on
the real portal — because the thing being tested is "a client with nothing but HTTP can run
the whole loop and watch it happen". A mocked engine would prove nothing about that.

The stream is checked the way the desk will use it: subscribe first, work second, and every
message that arrives must be an ``engine.events.Event`` the API did not reshape.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import chromium_or_skip

STREAM_TIMEOUT_SECONDS = 180.0
SUBSCRIBE_GRACE_SECONDS = 1.0

# Every field on engine.events.Event. If the API ever reshapes one, the desk breaks silently.
EVENT_FIELDS = {"kind", "message", "at", "exception_id", "fact", "step", "decision", "policy"}


@pytest.fixture
def client(world_urls: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """The app, pointed at the test world's ports rather than the demo's."""
    monkeypatch.setenv("TIEOUT_ERP_URL", world_urls["erp"])
    monkeypatch.setenv("TIEOUT_PORTAL_URL", world_urls["portal"])
    monkeypatch.setenv("TIEOUT_INBOX_URL", world_urls["inbox"])

    from tieout.api.main import app

    with TestClient(app) as opened:
        opened.post("/reset")
        yield opened


Message = tuple[str, dict[str, Any]]


def _read_stream(client: TestClient, exception_id: str, into: list[Message]) -> None:
    """Read one SSE stream to its ``done`` message. Blocking, so callers give it a thread."""
    kind = ""
    with client.stream("GET", f"/exceptions/{exception_id}/events") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("event: "):
                kind = line[len("event: ") :].strip()
            elif line.startswith("data: "):
                into.append((kind, json.loads(line[len("data: ") :])))
                if kind == "done":
                    return


def _work_and_watch(client: TestClient, exception_id: str, *, portal: bool = True) -> list[Message]:
    """Subscribe, then start the investigation — the order the desk uses."""
    received: list[Message] = []
    reader = threading.Thread(
        target=_read_stream, args=(client, exception_id, received), daemon=True
    )
    reader.start()
    time.sleep(SUBSCRIBE_GRACE_SECONDS)

    started = client.post(f"/exceptions/{exception_id}/work", params={"portal": portal})
    assert started.status_code == 202
    assert started.json()["state"] == "running"

    reader.join(timeout=STREAM_TIMEOUT_SECONDS)
    assert not reader.is_alive(), f"the stream for {exception_id} never closed"
    assert received and received[-1][0] == "done", "a stream must end with a done message"
    assert received[-1][1]["state"] == "done", received[-1][1]["error"]
    return received


def _kinds(messages: list[Message]) -> list[str]:
    return [kind for kind, _ in messages]


def _steps(messages: list[Message]) -> list[str]:
    return [payload["step"]["action"] for kind, payload in messages if kind == "step"]


def test_the_queue_is_the_five_exceptions(client: TestClient) -> None:
    body = client.get("/queue").json()

    assert body["count"] == 5
    assert [row["exception"]["kind"] for row in body["exceptions"]] == [
        "short_ship",
        "short_ship",
        "price_variance",
        "missing_po",
        "unknown",
    ]
    assert all(row["exception"]["status"] == "open" for row in body["exceptions"])
    assert all(row["decision"] is None for row in body["exceptions"])


def test_the_stream_carries_the_portal_sign_in_and_engine_events_unchanged(
    client: TestClient,
) -> None:
    """Beat one: the browser signs in on camera, and every message is an engine Event."""
    chromium_or_skip()
    client.get("/queue")

    messages = _work_and_watch(client, "E1")

    assert "signed in to VendorLink as" in " ".join(_steps(messages))
    assert _kinds(messages)[0] == "investigating"
    assert "proposed" in _kinds(messages)

    for kind, payload in messages:
        if kind == "done":
            continue
        assert set(payload) == EVENT_FIELDS, f"the API reshaped a {kind} event"
        assert payload["kind"] == kind, "the SSE event name is the engine's own kind"
        assert payload["exception_id"] == "E1"

    facts = [payload["fact"] for kind, payload in messages if kind == "fact"]
    portal_facts = [fact for fact in facts if fact["source"] == "portal"]
    assert portal_facts, "a short-ship has to be settled on the supplier's own document"
    assert all(fact["screenshot"] for fact in portal_facts)

    detail = client.get("/exceptions/E1").json()
    assert detail["pack"] is not None
    assert len(detail["pack"]["facts"]) == len(facts)
    assert detail["decision"]["action"] == "short_pay"
    assert detail["decision"]["confidence"] >= 0.7


def test_one_decision_teaches_the_rule_that_clears_the_next_one(client: TestClient) -> None:
    """Beats two and three: approve once, and the second short-ship never reaches a person."""
    chromium_or_skip()
    client.get("/queue")
    _work_and_watch(client, "E1")

    decided = client.post(
        "/exceptions/E1/decide",
        json={"action": "approve", "by": "Chris, Controller"},
    )
    assert decided.status_code == 200
    learned = decided.json()["policy"]
    assert learned["approved_by"] == "Chris, Controller"
    assert learned["learned_from"] == "E1"
    assert learned["version"] == 1
    assert decided.json()["exception"]["status"] == "resolved"

    messages = _work_and_watch(client, "E2")
    assert "auto_cleared" in _kinds(messages)
    cleared = next(payload for kind, payload in messages if kind == "auto_cleared")
    assert cleared["policy"]["id"] == learned["id"]
    assert cleared["decision"]["auto"] is True
    assert cleared["decision"]["cited_policy"] == f"{learned['id']} v{learned['version']}"
    assert cleared["decision"]["approved_by"] == "Chris, Controller"

    detail = client.get("/exceptions/E2").json()
    assert detail["exception"]["status"] == "auto_cleared"
    assert detail["policy"]["id"] == learned["id"], "the desk gets the rule, not just its name"

    rules = client.get("/policies").json()
    assert rules["count"] == 1
    assert rules["policies"][0]["cited_by"] == ["E2"]

    counters = client.get("/metrics").json()
    assert counters["human_touches"] == 1, "one approval cleared two exceptions"
    assert counters["auto_cleared"] == 1
    assert counters["touches_avoided_by_policy"] == 1


def test_the_refusal_is_a_first_class_answer_over_http(client: TestClient) -> None:
    """Beat four: nothing lines up, so the API hands it back rather than guessing."""
    chromium_or_skip()
    client.get("/queue")

    messages = _work_and_watch(client, "E5")

    assert "refused" in _kinds(messages)
    refusal = next(payload for kind, payload in messages if kind == "refused")
    assert refusal["decision"]["action"] == "refuse"
    assert "You decide." in refusal["decision"]["rationale"]

    detail = client.get("/exceptions/E5").json()
    assert detail["exception"]["status"] == "refused"
    assert [step for step in detail["pack"]["steps"] if not step["found"]], (
        "a refusal has to show the places that held nothing"
    )
    assert client.get("/policies").json()["count"] == 0, "a refusal never becomes a rule"


def test_the_api_refuses_to_run_two_investigations_at_once(client: TestClient) -> None:
    """The browser and the saved session are one shared resource, so this is a 409."""
    chromium_or_skip()
    client.get("/queue")

    received: list[Message] = []
    reader = threading.Thread(target=_read_stream, args=(client, "E1", received), daemon=True)
    reader.start()
    time.sleep(SUBSCRIBE_GRACE_SECONDS)

    assert client.post("/exceptions/E1/work").status_code == 202
    second = client.post("/exceptions/E2/work")
    assert second.status_code == 409
    assert "E1" in second.json()["detail"]
    assert client.post("/reset").status_code == 409, "a reset mid-investigation would lose it"

    reader.join(timeout=STREAM_TIMEOUT_SECONDS)
    assert client.post("/exceptions/E2/work").status_code == 202


def test_nothing_is_decided_without_an_evidence_pack(client: TestClient) -> None:
    client.get("/queue")

    refused = client.post(
        "/exceptions/E3/decide", json={"action": "approve", "by": "Chris, Controller"}
    )
    assert refused.status_code == 409
    assert "has not been investigated" in refused.json()["detail"]

    assert client.get("/exceptions/NOPE").status_code == 404
    assert (
        client.post("/exceptions/E3/decide", json={"action": "delete", "by": "Chris"}).status_code
        == 422
    )
    assert client.post("/exceptions/E3/decide", json={"action": "approve"}).status_code == 422


def test_reset_puts_the_world_and_the_memory_back(client: TestClient) -> None:
    client.get("/queue")
    messages = _work_and_watch(client, "E4", portal=False)
    assert "proposed" in _kinds(messages) or "refused" in _kinds(messages)
    assert client.get("/metrics").json()["worked"] == 1

    body = client.post("/reset").json()
    assert body["world"]["counts"]["invoices"] == 40

    counters = client.get("/metrics").json()
    assert counters["worked"] == 0
    assert counters["evidence_items"] == 0
    assert counters["policies_active"] == 0
    assert client.get("/queue").json()["count"] == 5
