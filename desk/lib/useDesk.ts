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

import type {
  DecidableAction,
  EngineEvent,
  ExceptionDetail,
  Fact,
  LookupStep,
  Metrics,
  PolicyRow,
  QueueRow,
} from "./api-types";
import {
  ApiError,
  decideException,
  getException,
  getMetrics,
  getPolicies,
  getQueue,
  resetWorld,
  streamException,
  workException,
} from "./api";

/** One live investigation: whose it is, and everything it has emitted so far. */
interface LiveRun {
  id: string;
  events: EngineEvent[];
}

export type Pending = "work" | "decide" | "reset" | null;

export interface Desk {
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
  approver: string;
  setApprover: (name: string) => void;
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

const DEFAULT_APPROVER = "Chris, Controller";

function say(failure: unknown): string {
  if (failure instanceof ApiError) return failure.message;
  return failure instanceof Error ? failure.message : String(failure);
}

export function useDesk(): Desk {
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExceptionDetail | null>(null);
  const [run, setRun] = useState<LiveRun | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [policies, setPolicies] = useState<PolicyRow[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [approver, setApprover] = useState(DEFAULT_APPROVER);
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

  /* ---------------------------------------------------------------- selecting */

  const select = useCallback(
    (id: string) => {
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
          onEvent: (event) =>
            setRun((current) =>
              current && current.id === id
                ? { id, events: [...current.events, event] }
                : current,
            ),
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
      const by = approver.trim();
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
          const answer = await decideException(id, { action, by, note });
          setLearned(answer.policy?.ref ?? null);
          setRun(null);
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
        const rows = await loadBoard();
        const first = rows[0]?.exception.id ?? null;
        selectedRef.current = first;
        setSelectedId(first);
        if (first) await loadDetail(first);
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

  const dismissError = useCallback(() => setError(null), []);

  return {
    queue,
    selectedId,
    detail,
    facts,
    steps,
    live,
    runningId,
    policies,
    metrics,
    approver,
    setApprover,
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
