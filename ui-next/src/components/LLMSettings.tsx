"use client";

import { useEffect, useState } from "react";

type Config = {
  provider: string;
  custom_url: string;
  custom_model: string;
  has_custom_key: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080";

export default function LLMSettings() {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [key, setKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetch(`${API}/llm/config`)
      .then((r) => r.json())
      .then(setCfg)
      .catch((e) => setMsg(`Load failed: ${e}`));
  }, []);

  async function save() {
    if (!cfg) return;
    setSaving(true);
    setMsg("");
    try {
      const r = await fetch(`${API}/llm/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: cfg.provider,
          custom_url: cfg.custom_url,
          custom_model: cfg.custom_model,
          custom_key: key || undefined,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Saved!");
      setKey("");
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  }

  if (!cfg) return <div className="text-slate-400">Loading LLM settings...</div>;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-6 mt-8">
      <h2 className="text-lg font-semibold text-white mb-4">LLM Provider</h2>

      <label className="block text-sm text-slate-300 mb-1">Provider</label>
      <select
        className="w-full mb-3 rounded bg-slate-800 border border-slate-700 p-2 text-white"
        value={cfg.provider}
        onChange={(e) => setCfg({ ...cfg, provider: e.target.value })}
      >
        <option value="custom">Custom (OpenAI-compatible)</option>
      </select>

      {cfg.provider === "custom" && (
        <>
          <label className="block text-sm text-slate-300 mb-1">Base URL</label>
          <input
            className="w-full mb-3 rounded bg-slate-800 border border-slate-700 p-2 text-white"
            value={cfg.custom_url}
            onChange={(e) => setCfg({ ...cfg, custom_url: e.target.value })}
            placeholder="https://api.groq.com/openai/v1"
          />

          <label className="block text-sm text-slate-300 mb-1">Model</label>
          <input
            className="w-full mb-3 rounded bg-slate-800 border border-slate-700 p-2 text-white"
            value={cfg.custom_model}
            onChange={(e) => setCfg({ ...cfg, custom_model: e.target.value })}
            placeholder="llama-3.3-70b-versatile"
          />

          <label className="block text-sm text-slate-300 mb-1">
            API Key {cfg.has_custom_key && <span className="text-green-400">(already set)</span>}
          </label>
          <input
            type="password"
            className="w-full mb-3 rounded bg-slate-800 border border-slate-700 p-2 text-white"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="gsk_..."
          />
        </>
      )}

      <button
        onClick={save}
        disabled={saving}
        className="mt-2 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save"}
      </button>

      {msg && <p className="mt-2 text-sm text-slate-300">{msg}</p>}
    </div>
  );
}
