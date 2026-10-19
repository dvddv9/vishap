# -*- coding: utf-8 -*-
"""Harness endpoints used by the UI badge (v7.0.0).

`GET /harness/status` is a cheap probe; `POST /harness/start` schedules
`ensure_harness()` in the background and returns immediately, because starting a
harness takes up to ~30 s and the caller is a button.
"""
import pytest
from fastapi.testclient import TestClient

import src.main as main


@pytest.fixture()
def client():
    return TestClient(main.app)


def test_status_returns_the_probe_shape(client, monkeypatch):
    monkeypatch.setattr(main, "harness_status", lambda **kw: {
        "url": "http://127.0.0.1:3080",
        "reachable": False,
        "started": False,
        "command": r"C:\dsh.cmd",
        "autostart": True,
        "error": "HARNESS_TOKEN empty",
    })
    body = client.get("/harness/status").json()
    assert body["reachable"] is False
    assert body["error"] == "HARNESS_TOKEN empty"
    assert set(body) == {"url", "reachable", "started", "command", "autostart", "error"}


def test_status_asks_for_a_fresh_probe(client, monkeypatch):
    seen = {}

    def fake_status(**kwargs):
        seen.update(kwargs)
        return {"url": "u", "reachable": True, "started": False,
                "command": None, "autostart": True, "error": None}

    monkeypatch.setattr(main, "harness_status", fake_status)
    assert client.get("/harness/status").json()["reachable"] is True
    assert seen.get("fresh") is True


def test_start_schedules_without_blocking(client, monkeypatch):
    called = []
    monkeypatch.setattr(main, "ensure_harness", lambda *a, **k: called.append(True))
    monkeypatch.setattr(main, "harness_status", lambda **kw: {
        "url": "http://127.0.0.1:3080", "reachable": False, "started": False,
        "command": "dsh", "autostart": True, "error": "refused",
    })

    response = client.post("/harness/start")
    assert response.status_code == 202
    assert response.json()["status"] == "starting"
    assert response.json()["harness"]["reachable"] is False
    # FastAPI runs background tasks after the response — and does run them.
    assert called == [True]


def test_start_reports_errors_from_the_background_task(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("spawn failed")

    monkeypatch.setattr(main, "ensure_harness", boom)
    monkeypatch.setattr(main, "harness_status", lambda **kw: {
        "url": "u", "reachable": False, "started": False,
        "command": None, "autostart": True, "error": None,
    })
    # The response must not turn into a 500 just because the start failed.
    assert client.post("/harness/start").status_code == 202
