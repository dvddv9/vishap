# -*- coding: utf-8 -*-
"""Sandbox for generated pytest code (v7.3.14).

WARNING: runs LLM-generated code. Use only with VISHAP_TESTER=1.
Limits: 5s timeout, no network, isolated temp dir.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_pytest_in_sandbox(test_code: str, timeout: int = 5) -> dict:
    """Run generated pytest test_code in isolated temp dir.

    Returns: {"ok": bool, "returncode": int, "stdout": str, "stderr": str, "reason": str}
    """
    if not test_code or not test_code.strip():
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "", "reason": "empty test_code"}

    tmp = tempfile.mkdtemp(prefix="vishap_sandbox_")
    test_file = Path(tmp) / "test_generated.py"
    try:
        test_file.write_text(test_code, encoding="utf-8")
        env = os.environ.copy()
        env["VISHAP_SANDBOX"] = "1"
        # disable network via env (best-effort; subprocess cannot fully block without container)
        env["http_proxy"] = "http://127.0.0.1:1"
        env["https_proxy"] = "http://127.0.0.1:1"
        env["NO_PROXY"] = ""
        cmd = [sys.executable, "-m", "pytest", str(test_file), "-q", "--no-header", "--tb=short"]
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.run(
            cmd, cwd=tmp, env=env, capture_output=True, text=True,
            timeout=timeout, **kwargs,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[:2000],
            "stderr": (proc.stderr or "")[:2000],
            "reason": "passed" if proc.returncode == 0 else "failed",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "", "reason": f"timeout {timeout}s"}
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": str(e), "reason": f"error: {e}"}
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
