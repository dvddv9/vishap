import Link from "next/link";
import { Shield, Zap, FileJson, ArrowRight } from "lucide-react";

export default function Hero({ canAnalyze }: { canAnalyze: boolean }) {
  return (
    <section className="relative overflow-hidden">
      {/* gradient background */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-sky-500/10 via-transparent to-emerald-500/10" />
      <div className="pointer-events-none absolute -top-40 -right-40 h-96 w-96 rounded-full bg-sky-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />

      <div className="relative mx-auto w-full max-w-6xl px-4 py-16 sm:py-20">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-xs text-slate-300 backdrop-blur">
          <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          Six-stage LLM pipeline · deterministic SAST/SCA
        </div>

        <h1 className="mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl lg:text-6xl">
          Security analysis for{" "}
          <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
            engineering materials
          </span>
        </h1>

        <p className="mt-4 max-w-2xl text-lg text-slate-400">
          Upload code, specs, logs, configs, or data. Get risks, STRIDE threat model,
          audit trail with SHA-256 provenance, and SARIF 2.1.0 export — in one report.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          {canAnalyze ? (
            <>
              <Link
                href="/analyze"
                className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/20 transition-all hover:shadow-xl hover:shadow-sky-500/30"
              >
                Analyze code
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
              <Link
                href="/analyze?example=sqli"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/60 px-6 py-3 text-sm font-medium text-slate-200 backdrop-blur transition-colors hover:border-slate-600 hover:text-slate-100"
              >
                Try example (SQLi)
              </Link>
            </>
          ) : (
            <Link
              href="/analyze"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/20"
            >
              Sign in to analyze
            </Link>
          )}
        </div>

        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          <Bullet icon={<Shield className="h-4 w-4" />} label="Deterministic SAST/SCA" />
          <Bullet icon={<Zap className="h-4 w-4" />} label="STRIDE threat model" />
          <Bullet icon={<FileJson className="h-4 w-4" />} label="SARIF 2.1.0 export" />
        </div>
      </div>
    </section>
  );
}

function Bullet({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-slate-800/60 bg-slate-900/40 px-4 py-3 text-sm text-slate-300 backdrop-blur">
      <span className="text-sky-400">{icon}</span>
      <span>{label}</span>
    </div>
  );
}
