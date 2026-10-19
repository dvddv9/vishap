# -*- coding: utf-8 -*-
"""Harness client - direct DSH (DeepSeek Harness) integration."""
from __future__ import annotations

import io
import json
import os
import time
import uuid
from pathlib import Path

import httpx
import zstandard

DEFAULT_URL = os.getenv("HARNESS_URL", "http://127.0.0.1:3080")
DEFAULT_TOKEN = os.getenv("HARNESS_TOKEN", "")
POLL_INTERVAL = 1.0
POLL_TIMEOUT = 600.0


def _resolve_token(token: str | None) -> str:
    """Explicit token > `HARNESS_TOKEN` > whichever candidate the harness accepts.

    `dsh web` issues a fresh token on every start, so a static `.env` value goes
    stale as soon as the launcher starts the harness itself — that is what
    produced `auth failed: HTTP 401` in the desktop app. The launcher probes the
    candidates and returns the one that actually authenticates.
    """
    if token:
        return token.strip()
    if DEFAULT_TOKEN.strip():
        return DEFAULT_TOKEN.strip()
    try:
        from src.llm.harness_launcher import pick_token

        return pick_token()[0]
    except Exception:
        return ""


class HarnessError(RuntimeError):
    """Any error talking to Harness (auth, RPC, filesystem)."""


class HarnessClient:
    """Synchronous client for a local DSH instance."""

    def __init__(self, url=DEFAULT_URL, token=DEFAULT_TOKEN, cwd=None, timeout=30.0):
        self.url = url.rstrip("/")
        self.token = _resolve_token(token)
        self.cwd = cwd or str(Path.cwd())
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)
        self._authed = False

    def _auth(self):
        if self._authed:
            return
        if not self.token:
            raise HarnessError("HARNESS_TOKEN empty")
        r = self._client.get(f"{self.url}/", params={"token": self.token})
        if r.status_code != 200:
            raise HarnessError(f"auth failed: HTTP {r.status_code}")
        self._authed = True

    def _rpc(self, method, args):
        self._auth()
        body = {"type": "client-request", "rpcId": str(uuid.uuid4()),
                "method": method, "payload": {"args": args}}
        r = self._client.post(f"{self.url}/api/{method}", json=body,
                              headers={"Content-Type": "application/json; charset=utf-8"})
        if r.status_code == 404:
            raise HarnessError(f"method not found: {method}")
        if r.status_code != 200:
            raise HarnessError(f"{method}: HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        result = data.get("result", {})
        if not result.get("ok", False):
            err = result.get("error", {})
            raise HarnessError(f"{method}: {err.get('code','?')}: {err.get('message','?')}")
        return result.get("value", {})

    def create_session(self, cwd=None):
        cwd = cwd or self.cwd
        value = self._rpc("session/create", {"request": {"cwd": cwd}})
        sid = value.get("sessionId")
        if not sid:
            raise HarnessError(f"no sessionId: {value}")
        return sid

    def send_prompt(self, session_id, message):
        self._rpc("session/prompt", {"request": {
            "requestId": str(uuid.uuid4()),
            "sessionId": session_id,
            "content": [{"type": "text", "text": message}],
            "mode": "queue",
            "clientTimeZone": "UTC",
        }})

    @staticmethod
    def _session_log_path(session_id, cwd):
        slug = cwd.replace(":", "").replace("\\", "-").replace("/", "-")
        slug = f"--{slug.strip('-')}--"
        base = Path.home() / ".dsh" / "sessions" / slug / session_id
        log = base / "session.v4.jsonl.zstd"
        if not log.exists():
            root = Path.home() / ".dsh" / "sessions"
            for cand in root.rglob(f"{session_id}/session.v4.jsonl.zstd"):
                return cand
        return log

    @staticmethod
    def _read_events(log_path):
        if not log_path.exists():
            return []
        raw = log_path.read_bytes()
        try:
            data = zstandard.ZstdDecompressor().stream_reader(
                io.BytesIO(raw)).read().decode("utf-8", errors="replace")
        except zstandard.ZstdError:
            data = zstandard.ZstdDecompressor().decompress(raw).decode("utf-8")
        events = []
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    @staticmethod
    def _extract_reply(events):
        for e in reversed(events):
            if e.get("type") != "assistant/message":
                continue
            content = (e.get("data") or {}).get("message", {}).get("content") or []
            parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            text = "\n".join(p for p in parts if p).strip()
            if text:
                return text
        return None

    def read_reply(self, session_id, cwd=None, timeout=POLL_TIMEOUT, interval=POLL_INTERVAL):
        cwd = cwd or self.cwd
        log_path = self._session_log_path(session_id, cwd)
        deadline = time.monotonic() + timeout
        last_seen = -1
        while time.monotonic() < deadline:
            events = self._read_events(log_path)
            if len(events) != last_seen:
                last_seen = len(events)
                reply = self._extract_reply(events)
                if reply:
                    return reply
            time.sleep(interval)
        raise HarnessError(f"timeout waiting for reply in {session_id}")

    def chat(self, user, system=None):
        full = f"{system}\n\n{user}" if system else user
        sid = self.create_session()
        self.send_prompt(sid, full)
        reply = self.read_reply(sid)
        return {"text": reply, "model": "harness", "tokens_in": 0,
                "tokens_out": 0, "mode": "harness"}

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()