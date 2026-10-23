import Link from "next/link";

export default function EmptyState() {
  return (
    <div className="mx-auto mt-4 max-w-2xl rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-sky-900/50 text-2xl">
        📄
      </div>
      <h3 className="text-lg font-semibold text-slate-100">No analyses yet</h3>
      <p className="mt-2 text-sm text-slate-400">
        Drop a file or paste code to see risks, threat model, and a SARIF report.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/analyze"
          className="rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-sky-400"
        >
          Analyze code →
        </Link>
        <Link
          href="/analyze?example=sqli"
          className="rounded-lg border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-800"
        >
          Try example (SQLi)
        </Link>
      </div>
    </div>
  );
}
