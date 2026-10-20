"use client";

import useSWR from "swr";
import { getHarnessStatus } from "@/lib/api";
import type { HarnessStatus } from "@/lib/types";

/** Poll slowly when idle. */
const POLL_IDLE_MS = 15_000;

type Tone = "ok" | "down" | "unknown";

const DOT: Record<Tone, string> = {
  ok: "bg-emerald-500",
  down: "bg-rose-500",
  unknown: "bg-slate-600",
};

/**
 * Harness indicator for the navbar (read-only).
 *
 * Shows whether the DSH harness is answering. Starting it is no longer done from
 * the UI: switch `LLM: harness` in ModeSwitch only makes sense when a harness
 * is already running, and `LLM: deepseek` does not need one at all.
 */
export default function HarnessBadge() {
  const { data, error } = useSWR<HarnessStatus>("/harness/status", getHarnessStatus, {
    refreshInterval: POLL_IDLE_MS,
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

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
  const tone: Tone = reachable === undefined ? "unknown" : reachable ? "ok" : "down";
  const label = reachable === undefined ? "Harness" : reachable ? "Harness" : "Harness off";
  const title = reachable
    ? `DSH harness is answering at ${data?.url ?? "HARNESS_URL"}`
    : `DSH harness is not answering${data?.error ? `: ${data.error}` : ""}`;

  return (
    <span className="flex items-center gap-1" title={title}>
      <span className="flex items-center gap-1.5 rounded-md border border-slate-800 px-2 py-1 text-[0.7rem] font-medium uppercase tracking-wide text-slate-400">
        <span className={`h-1.5 w-1.5 rounded-full ${DOT[tone]}`} aria-hidden="true" />
        <span className="hidden sm:inline">{label}</span>
        <span className="sm:hidden">H</span>
      </span>
    </span>
  );
}
