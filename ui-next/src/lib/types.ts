/**
 * Shared API contracts.
 *
 * These mirror the FastAPI responses in `src/main.py` — keep them in sync:
 *   POST /analyze/async  -> AnalyzeResponse
 *   GET  /status/{id}    -> Job      (never carries the report itself)
 *   GET  /report/{id}    -> Report   (409 until the job is done)
 */

export type JobStatus = "queued" | "running" | "done" | "failed";

export interface Job {
  job_id: string;
  status: JobStatus;
  filename: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
}

export interface AnalyzeResponse {
  job_id: string;
  status: JobStatus;
}

/** The slice of the audit trail the UI surfaces. */
export interface AuditSummary {
  critique_verdict?: string;
  risk_verdict?: string;
  cwe_ids?: string[];
  owasp_categories?: string[];
  [key: string]: unknown;
}

/** `GET /report/{id}` returns the flat pipeline result, not a `{ result: ... }` wrapper. */
export interface Report {
  session_id: string;
  timestamp: string;
  filename: string;
  final_markdown: string;
  critique_verdict?: string;
  material_size?: number;
  cost_usd?: number;
  audit?: AuditSummary;
  [key: string]: unknown;
}

export const TERMINAL_STATUSES: readonly JobStatus[] = ["done", "failed"];

export function isTerminal(status: JobStatus): boolean {
  return TERMINAL_STATUSES.includes(status);
}

/**
 * The DSH harness — the only LLM path.
 *
 * `GET /harness/status` returns this object directly; `/health` nests it under
 * `harness`. `reachable === false` means every analysis will fail with
 * `[LLM error]`, so the UI surfaces it in the navbar.
 */
export interface HarnessStatus {
  url: string;
  reachable: boolean;
  started: boolean;
  /** Path to the dsh CLI when it was found, otherwise null. */
  command: string | null;
  autostart: boolean;
  /** Why the probe failed — shown as a tooltip. */
  error: string | null;
}
