# -*- coding: utf-8 -*-
"""The Docker distribution must stay consistent with the app.

Docker support was removed in v7 and then restored by request, so these tests
pin the parts that silently rot: the image must run the API (not the removed
Streamlit UI), the compose stack must not try to start a harness inside the
container, and CI must build without publishing.
"""
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCKERFILE = ROOT / "Dockerfile"
COMPOSE = ROOT / "docker-compose.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "docker-build.yml"


def test_image_runs_the_api_only():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert 'CMD ["python", "-m", "src.main"]' in text
    assert "EXPOSE 5001" in text
    assert "8501" not in text, "the Streamlit UI was removed in v7"
    assert "streamlit" not in text.lower()
    assert "HEALTHCHECK" in text and "/health" in text
    assert "USER vishap" in text, "the container must not run as root"


def test_compose_wires_the_harness_to_the_host():
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = compose["services"]
    assert set(services) == {"api", "worker", "postgres", "redis"}
    for name in ("api", "worker"):
        env = services[name]["environment"]
        joined = "\n".join(env) if isinstance(env, list) else json.dumps(env)
        assert "HARNESS_AUTOSTART=0" in joined, (
            "the container cannot start a harness that lives on the host"
        )
        assert "host.docker.internal" in joined
        assert "HARNESS_URL" in joined


def test_compose_has_no_removed_services():
    text = COMPOSE.read_text(encoding="utf-8").lower()
    for removed in ("ollama", "streamlit", "grafana", "tempo"):
        assert removed not in text, f"{removed} was removed in v7"


def test_ci_builds_without_publishing():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    step = workflow["jobs"]["build"]["steps"][1]
    assert step["with"]["push"] is False, (
        "publishing needs a deliberate decision (and Docker Hub secrets)"
    )
    assert step["with"]["file"] == "./Dockerfile"
