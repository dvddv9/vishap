# -*- coding: utf-8 -*-
"""Harness autostart + `/health` visibility (v7.0.0).

The harness is the only LLM path, so these tests pin the three behaviours that
keep it from becoming a silent failure:

1. it is located and started only when it is local and autostart is on;
2. a dead harness produces a clear error, never an exception;
3. `/health` reports it.
"""
import pytest

from src.llm import harness_launcher as hl


@pytest.fixture(autouse=True)
def _clean_state():
    hl.reset_state()
    yield
    hl.reset_state()


# --- locating the CLI ------------------------------------------------------

def test_harness_cmd_env_wins(monkeypatch):
    monkeypatch.setenv("HARNESS_CMD", r"C:\custom\dsh.cmd")
    assert hl.find_harness_command() == r"C:\custom\dsh.cmd"


def test_find_harness_command_from_path(monkeypatch):
    monkeypatch.delenv("HARNESS_CMD", raising=False)
    monkeypatch.setattr(hl.shutil, "which", lambda name: "/usr/local/bin/dsh" if name == "dsh" else None)
    assert hl.find_harness_command() == "/usr/local/bin/dsh"


def test_find_harness_command_missing(monkeypatch):
    monkeypatch.delenv("HARNESS_CMD", raising=False)
    monkeypatch.setattr(hl.shutil, "which", lambda name: None)
    monkeypatch.setattr(hl.sys, "platform", "linux")  # skip the Windows install path
    assert hl.find_harness_command() is None


# --- local vs remote -------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("http://127.0.0.1:3080", True),
    ("http://localhost:3080", True),
    ("http://[::1]:3080", True),
    ("https://api.example.com", False),
    ("not a url", False),
])
def test_is_local_url(url, expected):
    assert hl.is_local_url(url) is expected


def test_autostart_defaults_on(monkeypatch):
    monkeypatch.delenv("HARNESS_AUTOSTART", raising=False)
    assert hl.autostart_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off"])
def test_autostart_can_be_disabled(monkeypatch, value):
    monkeypatch.setenv("HARNESS_AUTOSTART", value)
    assert hl.autostart_enabled() is False


# --- probing ---------------------------------------------------------------

def test_probe_without_token_is_a_clear_error(monkeypatch):
    ok, err = hl.probe("http://127.0.0.1:3080", token="")
    assert ok is False
    assert "HARNESS_TOKEN" in err


def test_probe_returns_true_on_200(monkeypatch):
    class R:
        status_code = 200
    monkeypatch.setattr(hl.httpx, "get", lambda *a, **k: R())
    assert hl.probe("http://127.0.0.1:3080", token="t") == (True, None)


def test_probe_swallows_exceptions(monkeypatch):
    def boom(*a, **k):
        raise OSError("connection refused")
    monkeypatch.setattr(hl.httpx, "get", boom)
    ok, err = hl.probe("http://127.0.0.1:3080", token="t")
    assert ok is False
    assert "connection refused" in err


# --- ensure_harness --------------------------------------------------------

def test_ensure_harness_no_spawn_when_already_up(monkeypatch):
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (True, None))
    spawned = []
    monkeypatch.setattr(hl, "_spawn", lambda *a, **k: spawned.append(a))
    result = hl.ensure_harness(autostart=True)
    assert result["reachable"] is True
    assert result["started"] is False
    assert spawned == []


def test_ensure_harness_spawns_and_waits(monkeypatch):
    # No candidate token authenticates -> the launcher has to start the harness.
    monkeypatch.setattr(hl, "pick_token", lambda *a, **k: ("", "refused"))
    monkeypatch.setattr(hl, "find_harness_command", lambda: "dsh")
    monkeypatch.setattr(hl, "is_local_url", lambda url: True)
    monkeypatch.setattr(hl.time, "sleep", lambda s: None)
    state = {"n": 0}

    def flaky_probe(*a, **k):
        state["n"] += 1
        return (True, None) if state["n"] > 1 else (False, "refused")

    monkeypatch.setattr(hl, "probe", flaky_probe)
    # The spawned harness prints its one-time token; the launcher must use it.
    monkeypatch.setattr(hl, "token_from_spawn_log", lambda: "tok-123")
    spawned = []
    monkeypatch.setattr(hl, "_spawn", lambda cmd, **k: spawned.append(cmd))

    result = hl.ensure_harness(autostart=True, timeout=5)
    assert spawned == ["dsh"]
    assert result["started"] is True
    assert result["reachable"] is True
    assert result["token"] == "tok-123"


def test_pick_token_prefers_a_token_that_authenticates(monkeypatch):
    monkeypatch.setattr(hl, "candidate_tokens", lambda: ["stale", "fresh"])
    seen = []

    def probe_with(url, token, timeout=hl.PROBE_TIMEOUT):
        seen.append(token)
        return (token == "fresh", None if token == "fresh" else "HTTP 401")

    monkeypatch.setattr(hl, "probe", probe_with)
    monkeypatch.setattr(hl, "save_token", lambda token: None)
    hl._WORKING_TOKEN = ""
    token, err = hl.pick_token()
    assert token == "fresh"
    assert err is None
    assert seen == ["stale", "fresh"]


def test_ensure_harness_reports_missing_cli(monkeypatch):
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (False, "refused"))
    monkeypatch.setattr(hl, "find_harness_command", lambda: None)
    monkeypatch.setattr(hl, "is_local_url", lambda url: True)
    result = hl.ensure_harness(autostart=True)
    assert result["reachable"] is False
    assert "HARNESS_CMD" in result["error"]


def test_ensure_harness_never_starts_a_remote_harness(monkeypatch):
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (False, "refused"))
    monkeypatch.setattr(hl, "find_harness_command", lambda: "dsh")
    spawned = []
    monkeypatch.setattr(hl, "_spawn", lambda *a, **k: spawned.append(a))
    result = hl.ensure_harness(url="https://harness.example.com", autostart=True)
    assert spawned == []
    assert "remote" in result["error"]


def test_ensure_harness_respects_autostart_off(monkeypatch):
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (False, "refused"))
    spawned = []
    monkeypatch.setattr(hl, "_spawn", lambda *a, **k: spawned.append(a))
    result = hl.ensure_harness(autostart=False)
    assert spawned == []
    assert result["reachable"] is False


def test_ensure_harness_survives_spawn_failure(monkeypatch):
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (False, "refused"))
    monkeypatch.setattr(hl, "find_harness_command", lambda: "dsh")
    monkeypatch.setattr(hl, "is_local_url", lambda url: True)

    def boom(*a, **k):
        raise PermissionError("denied")
    monkeypatch.setattr(hl, "_spawn", boom)
    result = hl.ensure_harness(autostart=True)
    assert result["reachable"] is False
    assert "spawn failed" in result["error"]


# --- cached status for /health --------------------------------------------

def test_status_is_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (calls.append(1), (False, "x"))[1])
    hl.status()
    hl.status()
    assert len(calls) == 1


def test_status_refresh(monkeypatch):
    calls = []
    monkeypatch.setattr(hl, "probe", lambda *a, **k: (calls.append(1), (True, None))[1])
    hl.status()
    hl.status(fresh=True)
    assert len(calls) == 2


def test_health_reports_the_harness(monkeypatch):
    from fastapi.testclient import TestClient
    from src.main import app

    monkeypatch.setattr(hl, "probe", lambda *a, **k: (False, "HARNESS_TOKEN empty"))
    body = TestClient(app).get("/health").json()
    assert body["status"] == "ok"
    assert "harness" in body
    assert body["harness"]["reachable"] is False
    assert "HARNESS_TOKEN" in body["harness"]["error"]
