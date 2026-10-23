import Link from "next/link";

export default function EmptyState() {
  return (
    <div className="mx-auto mt-4 max-w-2xl rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-sky-50 text-2xl">
        📄
      </div>
      <h3 className="text-lg font-semibold text-slate-900">No analyses yet</h3>
      <p className="mt-2 text-sm text-slate-600">
        Drop a file or paste code to see risks, threat model, and a SARIF report.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/analyze"
          className="rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-sky-500/20 hover:shadow-lg hover:shadow-sky-500/30"
        >
          Analyze code →
        </Link>
        <Link
          href="/analyze?example=sqli"
          className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Try example (SQLi)
        </Link>
      </div>
    </div>
  );
}
