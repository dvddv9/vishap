## 🚀 Vishap v6.3.0 — Next.js Dashboard

This release completes the SaaS roadmap by adding a modern React-based UI (Next.js 16 + Tailwind + Clerk) to replace the Streamlit prototype.

### ✨ New Features
- **Next.js Dashboard (`ui-next/`):** Modern UI with Clerk authentication, analyze form with polling, and Markdown report view.
- **Dark Terminal Theme:** Tailwind CSS + custom `.markdown-body` styles.
- **TypeScript:** Full type safety, API client (`apiFetch<T>`), localStorage job cache.

### 🔧 Infrastructure & Fixes
- **PyPI Trusted Publishing:** `.github/workflows/publish.yml` (build + twine check + OIDC publish on tag `v*`).
- **CI Fix:** `vishap.yml` Quality Gate is now non-blocking (Ollama unavailable in GitHub Actions).
- **Version Sync:** `pyproject.toml`, `src/version.py`, `src/ui/streamlit_app.py` all at `6.3.0`.

### 🧪 Tests & Build
- **553 tests passed** (Python).
- **npm run build:** 3 routes (`/`, `/analyze`, `/report/[id]`) compiled successfully.

### 📦 Install
pip install vishap-analyzer==6.3.0
