"use client";

import { useCallback, useEffect, useState } from "react";
import useSWR from "swr";
import { Play, Zap } from "lucide-react";
import { getHarnessStatus, startHarness } from "@/lib/api";
import type { HarnessStatus } from "@/lib/types";

/** Poll slowly when idle, quickly while a start is in flight. */
const POLL_IDLE_MS = 15_000;
const POLL_STARTING_MS = 1_500;
/** Give up on a start after this long; the harness may need a manual look. */
const START_GIVE_UP_MS = 40_000;

type Tone = "ok" | "down" | "busy" | "unknown";

const DOT: Record<Tone, string> = {
  ok: "bg-emerald-500",
  down: "bg-rose-500",
  busy: "bg-amber-400 animate-pulse",
  unknown: "bg-slate-600",
};

/**
 * Harness indicator for the navbar.
 *
 * The harness is the only LLM path, so a dead one turns every analysis into
 * `[LLM error]`. This shows that state up front and offers the one action that
 * fixes it — starting `dsh web` through `POST /harness/start`.
 */
export default function HarnessBadge() {
  const [starting, setStarting] = useState(false);

  const { data, error, mutate } = useSWR<HarnessStatus>("/harness/status", getHarnessStatus, {
    refreshInterval: starting ? POLL_STARTING_MS : POLL_IDLE_MS,
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  // A start either succeeds (badge flips to ok) or silently does nothing, so
  // release the spinner on a timer instead of leaving the button dead forever.
  useEffect(() => {
    if (!starting) return;
    const timer = setTimeout(() => setStarting(false), START_GIVE_UP_MS);
    return () => clearTimeout(timer);
  }, [starting]);

  useEffect(() => {
    if (starting && data?.reachable) setStarting(false);
  }, [starting, data?.reachable]);

  const onStart = useCallback(async () => {
    setStarting(true);
    try {
      await startHarness();
      await mutate();
    } catch {
      setStarting(false);
    }
  }, [mutate]);

  // The API itself is unreachable — the badge must not claim the harness is down.
  if (error) {
    return (
      <span
        className="flex items-center gap-1.5 rounded-md border border-slate-800 px-2 py-1 text-[0.7rem] text-slate-500"
        title={`Cannot reach the Vishap API: ${error instanceof Error ? error.message : String(error)}`}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${DOT.unknown}`} aria-hidden="true" />
        API
      </span>
    );
  }

  const reachable = data?.reachable;
  const tone: Tone = starting ? "busy" : reachable === undefined ? "unknown" : reachable ? "ok" : "down";
  const label = starting ? "Starting" : reachable === undefined ? "Harness" : reachable ? "Harness" : "Harness off";
  const title = starting
    ? "Starting the DSH harness…"
    : reachable
      ? `DSH harness is answering at ${data?.url ?? "HARNESS_URL"}`
      : `DSH harness is not answering${data?.error ? `: ${data.error}` : ""}`;

  return (
    <span className="flex items-center gap-1" title={title}>
      <span className="flex items-center gap-1.5 rounded-md border border-slate-800 px-2 py-1 text-[0.7rem] font-medium uppercase tracking-wide text-slate-400">
        <span className={`h-1.5 w-1.5 rounded-full ${DOT[tone]}`} aria-hidden="true" />
        <span className="hidden sm:inline">{label}</span>
        <span className="sm:hidden">H</span>
      </span>

      {reachable === false && !starting ? (
        <button
          type="button"
          onClick={onStart}
          title="Start dsh web (POST /harness/start)"
          aria-label="Start the DSH harness"
          className="flex items-center gap-1 rounded-md bg-slate-800 px-2 py-1 text-[0.7rem] font-medium text-slate-200 transition-colors hover:bg-slate-700"
        >
          <Play className="h-3 w-3" aria-hidden="true" />
          Start
        </button>
      ) : null}

      {starting ? (
        <Zap className="h-3.5 w-3.5 text-amber-400" aria-hidden="true" />
      ) : null}
    </span>
  );
}
