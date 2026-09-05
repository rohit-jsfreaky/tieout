"""Where Tieout keeps what it found, what it decided, and what it learned.

SQLite at ``~/.tieout/engine.db`` (``TIEOUT_ENGINE_DB`` overrides it). One row per document,
the pydantic JSON in a ``doc`` column, plus the columns worth querying on. The engine store
is separate from the world's database on purpose: the world is the company's data, this is
the agent's own memory, and ``tieout reset`` wipes both.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from . import tieout_home
from .models import Decision, EvidencePack, ExceptionCase, ExceptionStatus, Policy

SCHEMA = """
CREATE TABLE IF NOT EXISTS exceptions (
    id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL, vendor_id TEXT NOT NULL,
    kind TEXT NOT NULL, status TEXT NOT NULL, detected_at TEXT NOT NULL, doc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS packs (
    exception_id TEXT PRIMARY KEY, finished_at TEXT, facts INTEGER NOT NULL,
    doc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, exception_id TEXT NOT NULL, action TEXT NOT NULL,
    auto INTEGER NOT NULL, approved_by TEXT, cited_policy TEXT, decided_at TEXT NOT NULL,
    doc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS policies (
    id TEXT NOT NULL, version INTEGER NOT NULL, kind TEXT NOT NULL, active INTEGER NOT NULL,
    approved_by TEXT NOT NULL, approved_at TEXT NOT NULL, doc TEXT NOT NULL,
    PRIMARY KEY (id, version)
);
"""


def db_path() -> Path:
    override = os.environ.get("TIEOUT_ENGINE_DB")
    return Path(override) if override else tieout_home() / "engine.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.executescript(SCHEMA)
    return conn


def reset() -> Path:
    """Forget everything: exceptions, packs, decisions, learned policies."""
    target = db_path()
    if target.exists():
        target.unlink()
    conn = connect(target)
    conn.close()
    return target


# --------------------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------------------


def save_exceptions(cases: list[ExceptionCase]) -> None:
    """Upsert the match result, keeping any status an earlier run already set."""
    conn = connect()
    try:
        known = {
            row["id"]: row["status"] for row in conn.execute("SELECT id, status FROM exceptions")
        }
        with conn:
            for case in cases:
                status = known.get(case.id, case.status.value)
                stored = case.model_copy(update={"status": ExceptionStatus(status)})
                conn.execute(
                    "INSERT INTO exceptions"
                    " (id, invoice_id, vendor_id, kind, status, detected_at, doc)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)"
                    " ON CONFLICT(id) DO UPDATE SET doc = excluded.doc, kind = excluded.kind",
                    (
                        stored.id,
                        stored.invoice_id,
                        stored.vendor_id,
                        stored.kind.value,
                        status,
                        stored.detected_at.isoformat(timespec="seconds"),
                        stored.model_dump_json(),
                    ),
                )
    finally:
        conn.close()


def list_exceptions() -> list[ExceptionCase]:
    conn = connect()
    try:
        rows = list(conn.execute("SELECT doc, status FROM exceptions ORDER BY id"))
    finally:
        conn.close()
    return [_case_with_status(row) for row in rows]


def get_exception(exception_id: str) -> ExceptionCase | None:
    conn = connect()
    try:
        rows = list(
            conn.execute(
                "SELECT doc, status FROM exceptions WHERE id = ? OR invoice_id = ?",
                (exception_id, exception_id),
            )
        )
    finally:
        conn.close()
    return _case_with_status(rows[0]) if rows else None


def _case_with_status(row: sqlite3.Row) -> ExceptionCase:
    case = ExceptionCase.model_validate_json(row["doc"])
    return case.model_copy(update={"status": ExceptionStatus(row["status"])})


def set_status(exception_id: str, status: ExceptionStatus) -> None:
    conn = connect()
    try:
        with conn:
            conn.execute(
                "UPDATE exceptions SET status = ? WHERE id = ?", (status.value, exception_id)
            )
    finally:
        conn.close()


# --------------------------------------------------------------------------------------
# Evidence packs
# --------------------------------------------------------------------------------------


def save_pack(pack: EvidencePack) -> None:
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO packs (exception_id, finished_at, facts, doc)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(exception_id) DO UPDATE SET"
                " finished_at = excluded.finished_at, facts = excluded.facts,"
                " doc = excluded.doc",
                (
                    pack.exception.id,
                    pack.finished_at.isoformat(timespec="seconds") if pack.finished_at else None,
                    len(pack.facts),
                    pack.model_dump_json(),
                ),
            )
    finally:
        conn.close()


def get_pack(exception_id: str) -> EvidencePack | None:
    conn = connect()
    try:
        rows = list(conn.execute("SELECT doc FROM packs WHERE exception_id = ?", (exception_id,)))
    finally:
        conn.close()
    return EvidencePack.model_validate_json(rows[0]["doc"]) if rows else None


def list_packs() -> list[EvidencePack]:
    conn = connect()
    try:
        rows = list(conn.execute("SELECT doc FROM packs ORDER BY exception_id"))
    finally:
        conn.close()
    return [EvidencePack.model_validate_json(row["doc"]) for row in rows]


# --------------------------------------------------------------------------------------
# Decisions — final outcomes only. A proposal lives on its pack until someone acts on it.
# --------------------------------------------------------------------------------------


def save_decision(decision: Decision) -> None:
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO decisions"
                " (exception_id, action, auto, approved_by, cited_policy, decided_at, doc)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    decision.exception_id,
                    decision.action.value,
                    1 if decision.auto else 0,
                    decision.approved_by,
                    decision.cited_policy,
                    decision.decided_at.isoformat(timespec="seconds"),
                    decision.model_dump_json(),
                ),
            )
    finally:
        conn.close()


def list_decisions(exception_id: str | None = None) -> list[Decision]:
    conn = connect()
    try:
        if exception_id:
            rows = list(
                conn.execute(
                    "SELECT doc FROM decisions WHERE exception_id = ? ORDER BY id",
                    (exception_id,),
                )
            )
        else:
            rows = list(conn.execute("SELECT doc FROM decisions ORDER BY id"))
    finally:
        conn.close()
    return [Decision.model_validate_json(row["doc"]) for row in rows]


def latest_decision(exception_id: str) -> Decision | None:
    decisions = list_decisions(exception_id)
    return decisions[-1] if decisions else None


# --------------------------------------------------------------------------------------
# Policies — every version is kept. An old rule is never deleted, only superseded.
# --------------------------------------------------------------------------------------


def save_policy(policy: Policy) -> None:
    conn = connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO policies"
                " (id, version, kind, active, approved_by, approved_at, doc)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(id, version) DO UPDATE SET"
                " active = excluded.active, doc = excluded.doc",
                (
                    policy.id,
                    policy.version,
                    policy.kind.value,
                    1 if policy.active else 0,
                    policy.approved_by,
                    policy.approved_at.isoformat(timespec="seconds"),
                    policy.model_dump_json(),
                ),
            )
    finally:
        conn.close()


def retire_policy(policy: Policy, at: datetime) -> None:
    """Keep the row, mark it superseded. The audit trail needs the rule that used to apply."""
    superseded = policy.model_copy(update={"active": False, "superseded_at": at})
    save_policy(superseded)


def list_policies(active_only: bool = False) -> list[Policy]:
    conn = connect()
    try:
        sql = "SELECT doc FROM policies"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY id, version"
        rows = list(conn.execute(sql))
    finally:
        conn.close()
    return [Policy.model_validate_json(row["doc"]) for row in rows]


def get_policy(policy_id: str, version: int | None = None) -> Policy | None:
    versions = [p for p in list_policies() if p.id == policy_id]
    if version is not None:
        versions = [p for p in versions if p.version == version]
    return versions[-1] if versions else None
