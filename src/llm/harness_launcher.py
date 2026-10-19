# -*- coding: utf-8 -*-
"""Find, probe and (optionally) start a local DSH harness.

Vishap's only LLM path is the DeepSeek Harness, so a stale harness is the single
most likely reason for "the analysis returns nothing". This module makes that
failure visible and, when asked, fixes it:

- `find_harness_command()` — locate the `dsh` CLI (`HARNESS_CMD` wins, then PATH,
  then the Windows desktop install path).
- `probe()` — is the harness answering on `HARNESS_URL` with `HARNESS_TOKEN`.
- `ensure_harness()` — probe, and if it is down and ``HARNESS_AUTOSTART`` is on,
  spawn `dsh web` detached and poll until it answers (bounded).
- `status()` — cached snapshot for `/health` (no extra HTTP in the hot path).

Autostart is skipped unless the URL is loopback: starting a process on a host you
do not control is not this module's job.

CLI: ``python -m src.llm.harness_launcher`` prints the current status.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

from src.config import HARNESS_TOKEN, HARNESS_URL

#: How long to wait for a freshly spawned harness to answer.
DEFAULT_STARTUP_TIMEOUT = 30.0
POLL_INTERVAL = 1.0
PROBE_TIMEOUT = 1.5

#: `dsh web` prints its URL with a one-time token; that token is the only way in.
TOKEN_RE = re.compile(r"token=([A-Za-z0-9._~-]+)")

#: Must match the Tauri bundle identifier — the same directory the desktop shell
#: uses for logs and its WebView2 profile.
IDENTIFIER = "com.vishap.desktop"


def state_dir() -> Path:
    """`%LOCALAPPDATA%\\com.vishap.desktop` (written by the app, not by DSH)."""
    base = os.getenv("LOCALAPPDATA") or os.getenv("TMPDIR") or os.getenv("TEMP") or "."
    return Path(base) / IDENTIFIER


def spawn_log_path() -> Path:
    """Where the harness' own stdout/stderr goes when we start it."""
    return state_dir() / "logs" / "harness-spawn.log"


def token_file_path() -> Path:
    """The token discovered from a harness we started ourselves."""
    return state_dir() / "harness-token.txt"


def read_saved_token() -> str:
    """Token remembered from a previous autostart, if any."""
    try:
        return token_file_path().read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def save_token(token: str) -> None:
    """Remember the token so the next start (and `HarnessClient`) can use it."""
    try:
        path = token_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token, encoding="utf-8")
    except OSError:
        pass


def token_from_spawn_log() -> str:
    """Extract the token `dsh web` printed when we started it."""
    try:
        text = spawn_log_path().read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    matches = TOKEN_RE.findall(text)
    return matches[-1] if matches else ""


def resolve_token() -> str:
    """First *candidate* token: env, then the saved one, then the spawn log.

    Ordering is only a guess — `pick_token()` is what actually decides, because a
    token left in `.env` goes stale the moment the harness restarts.
    """
    return next(iter(candidate_tokens()), "")


def candidate_tokens() -> list[str]:
    """Every token we know about, de-duplicated, most trusted first."""
    seen: set[str] = set()
    out: list[str] = []
    for value in (HARNESS_TOKEN, read_saved_token(), token_from_spawn_log()):
        token = (value or "").strip()
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


#: Last token that authenticated, so `HarnessClient` does not re-probe every time.
_WORKING_TOKEN: str = ""


def pick_token(url: str | None = None,
               timeout: float = PROBE_TIMEOUT) -> tuple[str, str | None]:
    """Return ``(token, error)`` for the first candidate that authenticates.

    `dsh web` issues a new token on every start, so "the token in the file" is
    not a reliable answer — only a successful probe is.
    """
    global _WORKING_TOKEN
    if _WORKING_TOKEN:
        ok, _ = probe(url, _WORKING_TOKEN, timeout)
        if ok:
            return _WORKING_TOKEN, None

    last_error: str | None = None
    for token in candidate_tokens():
        ok, err = probe(url, token, timeout)
        if ok:
            _WORKING_TOKEN = token
            save_token(token)
            return token, None
        last_error = err
    return "", last_error or "HARNESS_TOKEN empty"

#: Candidate CLI locations, in priority order. `HARNESS_CMD` always wins.
_WINDOWS_CANDIDATES = (
    r"%LOCALAPPDATA%\Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd",
    r"%LOCALAPPDATA%\Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.exe",
)

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]", "0.0.0.0"}

#: How long a cached snapshot stays fresh in `/health` before it re-probes.
STATUS_TTL = 10.0

#: Cached snapshot for /health. `None` means "never probed".
_STATE: dict | None = None


def is_local_url(url: str) -> bool:
    """True when the harness runs on this machine (only then do we autostart)."""
    try:
        host = httpx.URL(url).host
    except Exception:
        return False
    return (host or "").lower() in _LOOPBACK_HOSTS


def autostart_enabled() -> bool:
    """``HARNESS_AUTOSTART`` defaults to on; set it to 0 on a shared server."""
    return os.getenv("HARNESS_AUTOSTART", "1").strip().lower() not in {"0", "false", "no", "off"}


def find_harness_command() -> str | None:
    """Path (or bare name) of the `dsh` CLI, or ``None`` when not installed."""
    override = os.getenv("HARNESS_CMD", "").strip()
    if override:
        return override

    for name in ("dsh", "dsh.cmd", "dsh.exe"):
        found = shutil.which(name)
        if found:
            return found

    if sys.platform == "win32":
        for template in _WINDOWS_CANDIDATES:
            path = Path(os.path.expandvars(template))
            if path.exists():
                return str(path)
    return None


def probe(url: str | None = None, token: str | None = None,
          timeout: float = PROBE_TIMEOUT) -> tuple[bool, str | None]:
    """Return ``(reachable, error)``. Never raises."""
    url = (url or HARNESS_URL).rstrip("/")
    token = HARNESS_TOKEN if token is None else token
    if not token:
        return False, "HARNESS_TOKEN empty"
    try:
        r = httpx.get(f"{url}/", params={"token": token}, timeout=timeout)
    except Exception as e:  # connection refused, DNS, timeout, ...
        return False, f"{type(e).__name__}: {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    return True, None


def _spawn(command: str, cwd: str | None = None) -> None:
    """Start ``dsh web`` detached and capture its output in a file.

    A pipe cannot be used: the child outlives us and would block on a full pipe.
    A file also gives us the **token** DSH prints at startup — without it every
    later request is `HTTP 401`. ``--no-open`` keeps it from popping a browser
    tab on every start.
    """
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    log = spawn_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w", encoding="utf-8", errors="replace") as out:
        subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            [command, "web", "--no-open"],
            cwd=cwd or str(Path.home()),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            close_fds=True,
        )


def listener_pid(url: str | None = None) -> int | None:
    """PID of the process listening on the harness port, if we can tell."""
    port = httpx.URL((url or HARNESS_URL)).port or 3080
    try:
        if sys.platform == "win32":
            out = subprocess.run(  # noqa: S603,S607 - fixed argv
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=5, check=False,
            ).stdout
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[0] == "TCP" and parts[1].endswith(f":{port}"):
                    if parts[3] == "LISTENING" and parts[4].isdigit():
                        return int(parts[4])
            return None
        out = subprocess.run(  # noqa: S603,S607 - fixed argv
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=5, check=False,
        ).stdout
        return int(out.strip().splitlines()[0]) if out.strip() else None
    except Exception:
        return None


def kill_listener(url: str | None = None) -> bool:
    """Stop a harness whose token we no longer know (it issued a new one)."""
    pid = listener_pid(url)
    if not pid:
        return False
    try:
        subprocess.run(  # noqa: S603,S607 - fixed argv
            ["taskkill", "/F", "/PID", str(pid)] if sys.platform == "win32"
            else ["kill", "-9", str(pid)],
            capture_output=True, timeout=10, check=False,
        )
        return True
    except Exception:
        return False


def restart_harness(command: str, url: str | None = None,
                    timeout: float = DEFAULT_STARTUP_TIMEOUT) -> dict:
    """Kill the harness we cannot authenticate to, start a fresh one, grab its token.

    `dsh web` prints a one-time token and keeps no copy we can read, so a harness
    started by an older build (or by hand) is unusable: the only recovery is a
    restart, which is exactly what this does.
    """
    killed = kill_listener(url)
    time.sleep(1.0)
    _spawn(command)
    deadline = time.monotonic() + timeout
    token = ""
    err = "harness did not print a token yet"
    while time.monotonic() < deadline:
        discovered = token_from_spawn_log()
        if discovered:
            token = discovered
            save_token(discovered)
        ok, err = probe(url, token)
        if ok:
            return {"reachable": True, "token": token, "restarted": True,
                    "killed": killed, "error": None}
        time.sleep(POLL_INTERVAL)
    return {"reachable": False, "token": token, "restarted": True,
            "killed": killed, "error": err}


def ensure_harness(url: str | None = None, token: str | None = None,
                   autostart: bool | None = None,
                   timeout: float = DEFAULT_STARTUP_TIMEOUT) -> dict:
    """Make sure the harness answers; start it if allowed. Never raises.

    Returns ``{"reachable", "started", "command", "url", "token", "error"}`` and
    refreshes the cached state used by :func:`status`.

    When the harness is started here, its one-time token is read back from
    ``logs/harness-spawn.log`` and remembered in ``harness-token.txt`` — that is
    what makes autostart actually usable instead of returning 401.
    """
    global _STATE
    url = (url or HARNESS_URL).rstrip("/")
    autostart = autostart_enabled() if autostart is None else autostart
    command = find_harness_command()
    result = {"url": url, "reachable": False, "started": False,
              "command": command, "autostart": autostart, "token": "",
              "error": None}

    # Try every known token before concluding the harness is down: a stale
    # `.env` value must not hide a harness that is running perfectly well.
    if token is None:
        token, err = pick_token(url)
    else:
        ok, err = probe(url, token)
        token = token if ok else ""

    if token:
        result["reachable"] = True
        result["token"] = token
        _STATE = result
        return result

    result["error"] = err
    if not autostart:
        _STATE = result
        return result
    if not is_local_url(url):
        result["error"] = f"harness is remote ({url}); not starting it"
        _STATE = result
        return result
    if not command:
        result["error"] = (f"{err}; cannot autostart - dsh CLI not found "
                           "(set HARNESS_CMD to its path)")
        _STATE = result
        return result

    try:
        _spawn(command)
        result["started"] = True
    except Exception as e:
        result["error"] = f"{err}; spawn failed: {type(e).__name__}: {e}"
        _STATE = result
        return result

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # The spawned harness issues a fresh token; pick it up as soon as it
        # appears, otherwise the probe keeps getting 401.
        discovered = token_from_spawn_log()
        if discovered and discovered != token:
            token = discovered
            save_token(discovered)
        ok, err = probe(url, token)
        if ok:
            if token and token != read_saved_token():
                save_token(token)
            result["reachable"] = True
            result["token"] = token
            result["error"] = None
            _STATE = result
            return result
        time.sleep(POLL_INTERVAL)

    # Still 401 with every token we have: the listener belongs to an instance
    # whose token we never saw. Restart it and take the fresh token.
    if err and "401" in err:
        restarted = restart_harness(command, url, timeout)
        result.update({k: v for k, v in restarted.items() if k != "token"})
        result["token"] = restarted.get("token", "")
        _STATE = result
        return result

    result["error"] = (f"{err}; harness did not answer within {timeout:.0f}s "
                       f"(autostart log: {spawn_log_path()})")
    _STATE = result
    return result


def status(fresh: bool = False, timeout: float = 0.3) -> dict:
    """Cached harness snapshot for `/health`; re-probes every ``STATUS_TTL`` seconds.

    The probe timeout is deliberately short: this runs inside the desktop's
    readiness loop, which polls `/health` with a sub-second socket timeout.
    """
    global _STATE
    stale = (_STATE is None
             or fresh
             or time.monotonic() - _STATE.get("checked_at", 0.0) > STATUS_TTL)
    if stale:
        ok, err = probe(timeout=timeout)
        _STATE = {
            "url": HARNESS_URL.rstrip("/"),
            "reachable": ok,
            "started": False,
            "command": find_harness_command(),
            "autostart": autostart_enabled(),
            "error": err,
            "checked_at": time.monotonic(),
        }
    return {k: v for k, v in _STATE.items() if k != "checked_at"}


def reset_state() -> None:
    """Forget the cached snapshot (used by tests)."""
    global _STATE
    _STATE = None


def main() -> int:
    s = status(fresh=True)
    print(f"harness url:      {s['url']}")
    print(f"reachable:        {s['reachable']}")
    print(f"command:          {s['command'] or '(not found)'}")
    print(f"autostart:        {s['autostart']}")
    if s["error"]:
        print(f"error:            {s['error']}")
    return 0 if s["reachable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
