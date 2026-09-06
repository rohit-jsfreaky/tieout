"use client";

/**
 * The desk's whole state, in one hook.
 *
 * It holds what the API said and what the stream has said since — nothing else.
 * There is no rule here, no threshold and no confidence: when this file needs a
 * judgement it asks the API for one. Merging the live events into the fetched
 * pack is the only cleverness, and it is only ever de-duplication.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import type {
  AuthorityRow,
  DecidableAction,
  EngineEvent,
  ExceptionDetail,
  Fact,
  LookupStep,
  Metrics,
  PolicyRow,
  QueueRow,
  Role,
  Source,
} from "./api-types";
import {
  ApiError,
  decideException,
  getAuthority,
  getException,
  getMetrics,
  getPolicies,
  getQueue,
  resetWorld,
  streamException,
  workException,
} from "./api";

/** The five things a person can be looking at. The sidebar is this list. */
export type View = "queue" | "exception" | "policies" | "audit" | "settings";

/** One live investigation: whose it is, and everything it has emitted so far. */
interface LiveRun {
  id: string;
  events: EngineEvent[];
}

export type Pending = "work" | "decide" | "reset" | null;

/**
 * One line of the audit trail: a fact that was observed, a decision that was
 * recorded, or a rule that was learned. Assembled from what the API returned —
 * every field below is copied off an engine object, never computed here.
 */
export interface AuditEntry {
  key: string;
  at: string;
  kind: "fact" | "decision" | "policy";
  exceptionId: string;
  subject: string;
  what: string;
  source: Source | null;
  locator: string | null;
  by: string;
  screenshot: string | null;
  auto: boolean;
}

/**
 * Who is at the desk: a name AND a seat.
 *
 * The seat is never inferred from the name — `engine/authority.py` refuses to
 * guess what somebody may approve, and so does this screen.
 */
export interface Approver {
  name: string;
  role: Role;
}

export interface Desk {
  view: View;
  setView: (view: View) => void;
  queue: QueueRow[];
  selectedId: string | null;
  detail: ExceptionDetail | null;
  /** The pack's facts, plus anything the stream has added since. */
  facts: Fact[];
  steps: LookupStep[];
  /** Every message of the run being watched, newest last. */
  live: EngineEvent[];
  runningId: string | null;
  policies: PolicyRow[];
  metrics: Metrics | null;
  /** Every fact, decision and rule across every exception, oldest first. */
  audit: AuditEntry[];
  auditLoading: boolean;
  approver: Approver;
  setApprover: (approver: Approver) => void;
  /** The delegation-of-authority matrix, exactly as `GET /authority` sent it. */
  authority: AuthorityRow[];
  /** The engine's own sentence about where a real matrix comes from. */
  authorityNote: string;
  /**
   * The approver's own row in that matrix — `null` until it lands, so the screen
   * can say "—" rather than pretend an unknown limit is no limit.
   */
  approverSeat: AuthorityRow | null;
  /** The rule the last approval created, so its card can announce itself. */
  learned: string | null;
  pending: Pending;
  loading: boolean;
  error: string | null;
  dismissError: () => void;
  nextId: string | null;
  select: (id: string) => void;
  work: (id: string) => void;
  decide: (action: DecidableAction, note: string) => void;
  reset: () => void;
}

const DEFAULT_APPROVER: Approver = { name: "Chris", role: "Controller" };

function say(failure: unknown): string {
  if (failure instanceof ApiError) return failure.message;
  return failure instanceof Error ? failure.message : String(failure);
}

export function useDesk(): Desk {
  const [view, setView] = useState<View>("queue");
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExceptionDetail | null>(null);
  const [run, setRun] = useState<LiveRun | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [policies, setPolicies] = useState<PolicyRow[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [approver, setApprover] = useState<Approver>(DEFAULT_APPROVER);
  const [authority, setAuthority] = useState<AuthorityRow[]>([]);
  const [authorityNote, setAuthorityNote] = useState("");
  const [learned, setLearned] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const closeStream = useRef<(() => void) | null>(null);
  // Which exception is on screen, readable from a callback that was created
  // before the selection changed — a fetch or a stream that lands late must not
  // overwrite the pack somebody is looking at now.
  const selectedRef = useRef<string | null>(null);
  useEffect(() => {
    selectedRef.current = selectedId;
  }, [selectedId]);

  /* ------------------------------------------------------------------ reading */

  // Reads of the board are numbered, because two of them can be in the air at
  // once (one when a run starts, one when it ends). An older answer landing last
  // would put the previous beat's counters back on screen.
  const boardSeq = useRef(0);

  const loadBoard = useCallback(async () => {
    const seq = ++boardSeq.current;
    // The queue read is the one that runs the three-way match and fills the
    // store; the counters only count what is in there. Asked for in parallel
    // straight after a reset, /metrics answers from an empty store and the
    // whole strip reads zero. So: queue first, counters second. Always.
    const queued = await getQueue();
    const [ruled, counted] = await Promise.all([getPolicies(), getMetrics()]);
    if (seq === boardSeq.current) {
      setQueue(queued.exceptions);
      setPolicies(ruled.policies);
      setMetrics(counted);
    }
    return queued.exceptions;
  }, []);

  const loadDetail = useCallback(async (id: string) => {
    const found = await getException(id);
    // A slow answer for an exception nobody is looking at any more is stale.
    if (selectedRef.current === id) setDetail(found);
  }, []);

  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const rows = await loadBoard();
        if (!alive) return;
        const first = rows[0]?.exception.id ?? null;
        selectedRef.current = first;
        setSelectedId(first);
        if (first) await loadDetail(first);
      } catch (failure) {
        if (alive) setError(say(failure));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
      closeStream.current?.();
    };
  }, [loadBoard, loadDetail]);

  // The matrix is a constant of the engine, so it is read once. Nothing on this
  // screen ever states a limit that did not come out of this call — a number an
  // approval is blocked by is not a number a frontend gets to invent.
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const answer = await getAuthority();
        if (!alive) return;
        setAuthority(answer.matrix);
        setAuthorityNote(answer.note);
      } catch (failure) {
        if (alive) setError(say(failure));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  /* -------------------------------------------------------------------- audit */

  // The trail spans every exception, so it needs every pack. The board is five
  // rows, so five reads — and it is re-read whenever the counters move, which is
  // exactly when something new has happened to record.
  useEffect(() => {
    if (view !== "audit" || queue.length === 0) return;
    let alive = true;
    const read = async () => {
      setAuditLoading(true);
      try {
        const details = await Promise.all(
          queue.map((row) => getException(row.exception.id)),
        );
        if (alive) setAudit(trail(details, policies));
      } catch (failure) {
        if (alive) setError(say(failure));
      } finally {
        if (alive) setAuditLoading(false);
      }
    };
    void read();
    return () => {
      alive = false;
    };
  }, [view, queue, policies]);

  /* ---------------------------------------------------------------- selecting */

  const select = useCallback(
    (id: string) => {
      setView("exception");
      if (id === selectedRef.current) return;
      selectedRef.current = id;
      setSelectedId(id);
      setDetail(null);
      setLearned(null);
      void loadDetail(id).catch((failure: unknown) => setError(say(failure)));
    },
    [loadDetail],
  );

  /* ------------------------------------------------------------------ working */

  const work = useCallback(
    (id: string) => {
      if (pending) return;
      setError(null);
      setLearned(null);
      setPending("work");
      setView("exception");
      selectedRef.current = id;
      setSelectedId(id);
      setDetail(null);
      setRun({ id, events: [] });

      void (async () => {
        try {
          await workException(id);
        } catch (failure) {
          setError(say(failure));
          setPending(null);
          setRun(null);
          return;
        }
        setRunningId(id);
        void loadBoard().catch(() => undefined);

        // The run is only over when the counters agree that it is. Clearing
        // `pending` before the refetch lands leaves the screen readable but a
        // beat behind — the refusal on screen next to "Refused 0".
        const finish = (message?: string) => {
          closeStream.current = null;
          setRunningId(null);
          if (message) setError(message);
          void Promise.all([loadBoard(), loadDetail(id)])
            .catch((failure: unknown) => setError(say(failure)))
            .finally(() => setPending(null));
        };

        closeStream.current = streamException(id, {
          onEvent: (event) => {
            if (event.kind === "auto_cleared" && event.decision?.cited_policy) {
              toast.success(`${id} cleared itself`, {
                description: `${event.decision.cited_policy} · ${event.decision.approved_by}. Nobody was asked.`,
              });
            }
            setRun((current) =>
              current && current.id === id
                ? { id, events: [...current.events, event] }
                : current,
            );
          },
          onDone: (done) =>
            finish(done.state === "failed" ? done.error : undefined),
          onError: (message) => finish(message),
        });
      })();
    },
    [loadBoard, loadDetail, pending],
  );

  /* ----------------------------------------------------------------- deciding */

  const decide = useCallback(
    (action: DecidableAction, note: string) => {
      const id = selectedRef.current;
      const by = approver.name.trim();
      if (!id || pending) return;
      if (!by) {
        setError(
          "Put a name in the approver field. A rule with nobody on it is worthless.",
        );
        return;
      }
      setError(null);
      setPending("decide");

      void (async () => {
        try {
          // The seat travels with the name, always. The engine will not record a
          // decision whose authority nobody can check.
          const answer = await decideException(id, {
            action,
            by,
            role: approver.role,
            note,
          });
          setLearned(answer.policy?.ref ?? null);
          setRun(null);
          if (answer.policy) {
            toast.success(`${answer.policy.ref} learned`, {
              description: `${answer.policy.name} — approved by ${answer.policy.approved_by}.`,
            });
          }
          await Promise.all([loadBoard(), loadDetail(id)]);
        } catch (failure) {
          setError(say(failure));
        } finally {
          setPending(null);
        }
      })();
    },
    [approver, loadBoard, loadDetail, pending],
  );

  /* -------------------------------------------------------------------- reset */

  const reset = useCallback(() => {
    if (pending) return;
    setError(null);
    setPending("reset");
    closeStream.current?.();
    closeStream.current = null;

    void (async () => {
      try {
        await resetWorld();
        setRun(null);
        setRunningId(null);
        setLearned(null);
        setDetail(null);
        setAudit([]);
        const rows = await loadBoard();
        const first = rows[0]?.exception.id ?? null;
        selectedRef.current = first;
        setSelectedId(first);
        if (first) await loadDetail(first);
        toast.success("Back to the seed", {
          description:
            "The world, the learned rules, the saved portal session and the screenshots are all as they started.",
        });
      } catch (failure) {
        setError(say(failure));
      } finally {
        setPending(null);
      }
    })();
  }, [loadBoard, loadDetail, pending]);

  /* ------------------------------------------------- what the panels read from */

  const live = useMemo(
    () => (run && run.id === selectedId ? run.events : []),
    [run, selectedId],
  );

  const facts = useMemo(() => {
    const seen = new Set<string>();
    const merged: Fact[] = [];
    for (const fact of [
      ...(detail?.pack?.facts ?? []),
      ...live.flatMap((event) => (event.fact ? [event.fact] : [])),
    ]) {
      if (seen.has(fact.id)) continue;
      seen.add(fact.id);
      merged.push(fact);
    }
    return merged;
  }, [detail, live]);

  const steps = useMemo(() => {
    const seen = new Set<string>();
    const merged: LookupStep[] = [];
    for (const step of [
      ...(detail?.pack?.steps ?? []),
      ...live.flatMap((event) => (event.step ? [event.step] : [])),
    ]) {
      const key = `${step.source}|${step.action}|${step.locator}|${step.at}`;
      if (seen.has(key)) continue;
      seen.add(key);
      merged.push(step);
    }
    return merged;
  }, [detail, live]);

  const nextId = useMemo(
    () => queue.find((row) => row.exception.status === "open")?.exception.id ?? null,
    [queue],
  );

  const approverSeat = useMemo(
    () => authority.find((row) => row.role === approver.role) ?? null,
    [authority, approver.role],
  );

  const dismissError = useCallback(() => setError(null), []);

  return {
    view,
    setView,
    queue,
    selectedId,
    detail,
    facts,
    steps,
    live,
    runningId,
    policies,
    metrics,
    audit,
    auditLoading,
    approver,
    setApprover,
    authority,
    authorityNote,
    approverSeat,
    learned,
    pending,
    loading,
    error,
    dismissError,
    nextId,
    select,
    work,
    decide,
    reset,
  };
}

/**
 * Every fact, decision and rule in the order they happened.
 *
 * Flattening, not deriving: each line carries the timestamp the engine wrote on
 * the object it came from, and the sort is on that timestamp alone.
 */
function trail(details: ExceptionDetail[], policies: PolicyRow[]): AuditEntry[] {
  const entries: AuditEntry[] = [];

  for (const found of details) {
    const id = found.exception.id;
    const invoice = found.exception.invoice_id;

    for (const fact of found.pack?.facts ?? []) {
      entries.push({
        key: `fact:${fact.id}`,
        at: fact.observed_at,
        kind: "fact",
        exceptionId: id,
        subject: invoice,
        what: fact.statement,
        source: fact.source,
        locator: fact.locator,
        by: fact.extracted_by,
        screenshot: fact.screenshot,
        auto: false,
      });
    }

    const decision = found.decision;
    if (decision) {
      entries.push({
        key: `decision:${id}:${decision.decided_at}`,
        at: decision.decided_at,
        kind: "decision",
        exceptionId: id,
        subject: invoice,
        what: decision.summary,
        source: null,
        locator: decision.cited_policy,
        by: decision.approved_by ?? decision.rationale_by,
        screenshot: null,
        auto: decision.auto,
      });
    }
  }

  for (const row of policies) {
    entries.push({
      key: `policy:${row.policy.ref}`,
      at: row.policy.approved_at,
      kind: "policy",
      exceptionId: row.policy.learned_from,
      subject: row.policy.learned_from_invoice,
      what: `${row.policy.ref} — ${row.policy.name}`,
      source: null,
      locator: null,
      by: row.policy.approved_by,
      screenshot: null,
      auto: false,
    });
  }

  return entries.sort((a, b) => a.at.localeCompare(b.at));
}
