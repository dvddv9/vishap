# -*- coding: utf-8 -*-
"""Clean .env.example: remove duplicates, keep one provider block."""
from pathlib import Path
import re

P = Path(r"C:\Users\HP\vishap-7.0.1\.env.example")
t = P.read_text(encoding="utf-8")
orig = t

# 1) Remove old DSH block (lines 11-16: "=== LLM: custom (DSH endpoint via dsh-model-endpoint) ===")
t = re.sub(
    r'# === LLM: custom \(DSH endpoint via dsh-model-endpoint\).*?(?=\n#|\n\n|\Z)',
    '',
    t, flags=re.DOTALL,
)

# 2) Remove old "Custom LLM (OpenAI-compatible)" block (lines ~101-109)
t = re.sub(
    r'# === Custom LLM \(OpenAI-compatible\) ===.*?CUSTOM_LLM_MODEL=deepseek-chat\n',
    '',
    t, flags=re.DOTALL,
)

# 3) Remove old "Provider 2: DeepSeek Search/Fetch" comment lines (28-29) — keep DEEPSEEK_SEARCH_URL
t = re.sub(
    r'# Provider 2: DeepSeek Search/Fetch \(if CUSTOM_LLM_KEY set\)\n# Uses CUSTOM_LLM_KEY \(same as LLM\) — no extra key needed\.\n',
    '',
    t,
)

# 4) Remove blank lines duplication (3+ \n -> 2 \n)
t = re.sub(r'\n{3,}', '\n\n', t)

# 5) Ensure VISHAP_LLM_PROVIDER=custom is present (once)
if t.count("VISHAP_LLM_PROVIDER=custom") == 0:
    t = t.replace(
        "# === LLM: provider selection ===",
        "# === LLM: provider selection ===\nVISHAP_LLM_PROVIDER=custom",
        1,
    )

if t != orig:
    P.write_text(t, encoding="utf-8")
    print("patched: .env.example (deduplicated)")
else:
    print("no change")

# verify
print("--- .env.example (VISHAP_LLM_PROVIDER | CUSTOM_LLM_URL | DeepSeek | OpenAI | Groq | Ollama | DSH) ---")
for i, line in enumerate(t.splitlines(), 1):
    if any(x in line for x in ["VISHAP_LLM_PROVIDER", "CUSTOM_LLM_URL", "DeepSeek", "OpenAI", "Groq", "Ollama", "DSH"]):
        print(f"{i}: {line[:120]}")
print("DONE")
