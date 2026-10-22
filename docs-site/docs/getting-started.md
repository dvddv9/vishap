# Getting Started

Vishap is a 6-stage LLM pipeline that analyzes code, config, specs, logs, and data, and returns a structured Markdown report with risks, a STRIDE threat model, refactoring options, and an audit trail (SHA-256, PII detection, compliance flags, provenance).

## Prerequisites

- Python 3.11 or 3.12
- Node.js 18+ (for the UI)
- PostgreSQL 16 (for history and audit trail)
- One of the following LLM providers:
  - **Custom (OpenAI-compatible)**: Groq, OpenAI, Mistral, OpenRouter, Together
  - **Harness (DSH)**: local DeepSeek Harness
  - **DeepSeek (direct)**: direct API calls

## Install

```powershell
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
