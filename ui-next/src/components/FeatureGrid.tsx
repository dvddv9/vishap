import { ShieldCheck, Workflow, FileJson } from "lucide-react";

const features = [
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "Deterministic SAST/SCA",
    body: "Pattern-based rules run before the LLM, so critical findings (SQLi, RCE, XSS) are caught without hallucination.",
  },
  {
    icon: <Workflow className="h-5 w-5" />,
    title: "Six-stage pipeline",
    body: "Ingestion → Taint → Dataflow → Risk → Verdict → Report. Every stage is auditable and can be replayed.",
  },
  {
    icon: <FileJson className="h-5 w-5" />,
    title: "SARIF 2.1.0 + audit trail",
    body: "Export to GitHub Security / IDE. Each report carries SHA-256 provenance and a 90-day valid_until.",
  },
];

export default function FeatureGrid() {
  return (
    <section className="mx-auto w-full max-w-6xl px-4 pb-16">
      <div className="grid gap-4 sm:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="group rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur transition-all hover:border-slate-700 hover:bg-slate-900/60"
          >
            <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500/20 to-emerald-500/20 text-sky-400 group-hover:from-sky-500/30 group-hover:to-emerald-500/30">
              {f.icon}
            </div>
            <h3 className="text-base font-semibold text-slate-100">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
