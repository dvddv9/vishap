# -*- coding: utf-8 -*-
"""
Vishap Р Р†Р вЂљРІР‚Сњ FastAPI Р РЋР С“Р В Р’ВµР РЋР вЂљР В Р вЂ Р В Р’ВµР РЋР вЂљ.
"""
from contextlib import asynccontextmanager
from pathlib import Path
import json
import os
import threading
import time
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Query
from typing import Literal
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import APP_NAME, PORT, DATA_DIR, validate_config
from src.observability.logging import (
    setup_logging,
    get_logger,
    bind_request_id,
    clear_context,
)
from src.observability.metrics import get_metrics_output, observe_http_request
from src.observability.tracing import setup_tracing, traced
from src.pipeline.batch import run_batch
from src.storage.history import load_history
from src.api.auth import verify_api_key, is_auth_enabled
from src.api.rate_limit import rate_limit_analyze, rate_limit_read
from src.api.jobs import (
    create_job_async, get_job_async, update_job_async, delete_job_async,
)
from src.api.audit import DEFAULT_LIMIT, MAX_LIMIT, export_audit
from src.api.tasks import run_analysis_task
from src.api.celery_app import broker_available
from src.github_app.webhook import handle_webhook
from src.api.job_store import tenant_scope
from src.auth.middleware import current_tenant, current_user
from src.auth.sso import saml_callback, saml_login
from src.billing.stripe_client import create_checkout_session, create_invoice
from src.billing.stripe_setup import list_prices
from src.billing.webhook import handle_stripe_webhook_async
from src.api.gdpr import delete_user_data, export_user_data
from src.api.reports import InvalidReportPath, report_path, save_report
from src.api.webhooks import notify_webhook
from datetime import UTC
from src.tools.sarif import to_sarif
from src.llm.harness_launcher import autostart_enabled, ensure_harness, status as harness_status


def _start_harness_in_background() -> None:
    """Make the harness reachable without delaying API startup.

    The harness is the only LLM path, so a stale one would turn every analysis
    into `[LLM error]`. `ensure_harness()` probes first and only spawns `dsh web`
    when needed; it runs in a thread because startup can take up to ~30s.
    """
    if not autostart_enabled():
        return
    if "PYTEST_CURRENT_TEST" in os.environ:  # never spawn a real harness in tests
        return

    def _run() -> None:
        try:
            result = ensure_harness()
            if result["reachable"]:
                how = "started" if result["started"] else "already running"
                print(f"[harness] ready at {result['url']} ({how})")
            else:
                print(f"[harness] not reachable: {result['error']}")
        except Exception as e:  # never take the API down over the LLM
            print(f"[harness] autostart failed: {type(e).__name__}: {e}")

    threading.Thread(target=_run, name="harness-autostart", daemon=True).start()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast: missing DATABASE_URL / STRIPE_SECRET_KEY / CLERK_SECRET_KEY
    # stops the server here instead of surfacing as a 500 on the first request.
    # VISHAP_DEV=true downgrades this to a warning.
    validate_config()
    print(f"=== {APP_NAME} API Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р В РЎвЂќР В Р’В°Р В Р’ВµР РЋРІР‚С™Р РЋР С“Р РЋР РЏ ===")
    print(f"Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂќР РЋР вЂљР В РЎвЂўР В РІвЂћвЂ“ Р В Р вЂ  Р В Р’В±Р РЋР вЂљР В Р’В°Р РЋРЎвЂњР В Р’В·Р В Р’ВµР РЋР вЂљР В Р’Вµ: http://localhost:{PORT}/docs")
    _start_harness_in_background()
    yield
    print(f"=== {APP_NAME} API Р В РЎвЂўР РЋР С“Р РЋРІР‚С™Р В Р’В°Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦ ===")


# structlog: pretty in dev, JSON in prod (LOG_FORMAT=json)
setup_logging()
log = get_logger(__name__)

# OpenTelemetry tracing: fail-open if OTel is missing/disabled.
setup_tracing()


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Vishap V6.0.3 Р Р†Р вЂљРІР‚Сњ 6-Р РЋР С“Р РЋРІР‚С™Р В Р’В°Р В РўвЂР В РЎвЂР В РІвЂћвЂ“Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ LLM-Р В РЎвЂќР В РЎвЂўР В Р вЂ¦Р В Р вЂ Р В Р’ВµР В РІвЂћвЂ“Р В Р’ВµР РЋР вЂљ Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В°Р В Р вЂ¦Р В Р’В°Р В Р’В»Р В РЎвЂР В Р’В·Р В Р’В° Р В РЎвЂќР В РЎвЂўР В РўвЂР В Р’В°",
    version="6.4.0",
    lifespan=lifespan,
)

# CORS is applied as `cors_app` right before `__main__`, wrapping the *entire*
# stack (including ServerErrorMiddleware). It has to be an explicit outer wrap:
# `app.add_middleware` places CORS *inside* ServerErrorMiddleware, so an
# unhandled exception (a 500) would escape with no `Access-Control-Allow-Origin`
# and the desktop webview would report every failure as "blocked by CORS policy".
# See `cors_app = CORSMiddleware(app, ...)` at the bottom.

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())[:8]
    bind_request_id(request_id)
    start = time.time()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)
        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        observe_http_request(request.method, request.url.path, response.status_code)
        return response
    except Exception as e:
        duration_ms = round((time.time() - start) * 1000, 2)
        log.error(
            "http_request_error",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise
    finally:
        clear_context()


# === Pydantic-Р РЋР С“Р РЋРІР‚В¦Р В Р’ВµР В РЎВР РЋРІР‚в„– ===

class AnalyzeRequest(BaseModel):
    force: bool = False
    material: str = Field(..., description="Р В РЎв„ўР В РЎвЂўР В РўвЂ, spec, logs Р Р†Р вЂљРІР‚Сњ Р РЋРІР‚РЋР РЋРІР‚С™Р В РЎвЂў Р В Р’В°Р В Р вЂ¦Р В Р’В°Р В Р’В»Р В РЎвЂР В Р’В·Р В РЎвЂР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚С™Р РЋР Р‰")
    filename: str = Field(default="input.txt", description="Р В Р’ВР В РЎВР РЋР РЏ Р РЋРІР‚С›Р В Р’В°Р В РІвЂћвЂ“Р В Р’В»Р В Р’В° (Р В РўвЂР В Р’В»Р РЋР РЏ Р В РЎвЂќР В РЎвЂўР В Р вЂ¦Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋР С“Р РЋРІР‚С™Р В Р’В°)")
    verbose: bool = Field(default=False, description="Р В РЎСџР В РЎвЂўР В РўвЂР РЋР вЂљР В РЎвЂўР В Р’В±Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В Р’В»Р В РЎвЂўР В РЎвЂ“Р В РЎвЂ Р В Р вЂ  Р В РЎвЂўР РЋРІР‚С™Р В Р вЂ Р В Р’ВµР РЋРІР‚С™Р В Р’Вµ")


class AnalyzeResponse(BaseModel):
    session_id: str
    filename: str
    level: str | None = None
    route: list | None = None
    final_markdown: str
    timestamp: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    audit_id: str = ""
    material_hash: str = ""
    material_hash_full: str = ""
    truncated: bool = False
    original_size: int = 0
    verdict: str = ""
    pii_detected: bool = False
    compliance_flags: list = []
    audit: dict = {}
    completeness: dict = {}


class HistoryItem(BaseModel):
    session_id: str
    filename: str
    level: str | None = None
    route: list | None = None
    material_size: int
    timestamp: str
    verdict: str | None = None
    pii_detected: bool | None = None


class BatchItem(BaseModel):
    material: str = Field(..., description="Р В РЎв„ўР В РЎвЂўР В РўвЂ / spec / logs")
    filename: str = Field(default="input.txt", description="Р В Р’ВР В РЎВР РЋР РЏ Р РЋРІР‚С›Р В Р’В°Р В РІвЂћвЂ“Р В Р’В»Р В Р’В°")


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., description="Р В Р Р‹Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В РЎвЂўР В РЎвЂќ Р В РЎВР В Р’В°Р РЋРІР‚С™Р В Р’ВµР РЋР вЂљР В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂўР В Р вЂ ")
    max_concurrent: int = Field(default=3, ge=1, le=10,
                                description="Р В РЎС™Р В Р’В°Р В РЎвЂќР РЋР С“. Р В РЎвЂ”Р В Р’В°Р РЋР вЂљР В Р’В°Р В Р’В»Р В Р’В»Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р РЋРІР‚В¦ LLM-Р В Р вЂ Р РЋРІР‚в„–Р В Р’В·Р В РЎвЂўР В Р вЂ Р В РЎвЂўР В Р вЂ  (1..10)")


class BatchResponseItem(BaseModel):
    session_id: str | None = None
    filename: str
    level: str | None = None
    route: list | None = None
    final_markdown: str | None = None
    verdict: str | None = None
    pii_detected: bool | None = None
    error: str | None = None


class BatchResponse(BaseModel):
    results: list[BatchResponseItem]
    count: int
    max_concurrent: int


class ModeRequest(BaseModel):
    mode: str = Field(..., description="auto / cloud / local")


class ModeResponse(BaseModel):
    mode: str
    valid_modes: list[str]


# === Endpoints ===

@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": "5.9.6",
        "docs": "/docs",
        "endpoints": ["/analyze", "/history", "/health"],
    }


@app.get("/health")
async def health():
    # `harness` is the only LLM path: report it here so a dead harness is visible
    # from the health check instead of surfacing as "analysis returned nothing".
    # `harness_status()` is cached (refreshed by the startup autostart), so this
    # endpoint stays instant.
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "harness": harness_status(),
    }



class ModeRequest(BaseModel):
    mode: Literal["harness", "deepseek"]


@app.get("/harness/status")
async def harness_status_endpoint():
    """Fresh probe of the only LLM path.

    Short timeout (0.3 s) so the navbar can poll it without blocking.
    """
    return harness_status(fresh=True)


def _ensure_harness_safely() -> None:
    """Start the harness, never letting the failure escape the background task."""
    try:
        ensure_harness()
    except Exception as e:  # the button already got its 202; log and move on
        print(f"[harness] start failed: {type(e).__name__}: {e}")


@app.post("/harness/start", status_code=202)
def harness_start(background: BackgroundTasks):
    """Start ``dsh web`` when it is not answering.

    Returns immediately (``202``) and runs `ensure_harness()` in the background РІР‚вЂќ
    starting a harness can take ~30 s, and the caller is a UI button. The client
    polls `/harness/status` until `reachable` flips to true.
    """
    background.add_task(_ensure_harness_safely)
    return {"status": "starting", "harness": harness_status()}


@app.delete("/status/{job_id}", dependencies=[Depends(verify_api_key), Depends(rate_limit_read)])
async def delete_status(job_id: str, tenant: str = Depends(current_tenant)):
    """Forget a job РІР‚вЂќ what the UI's delete button calls.

    Removes the job record (status/report lookups then answer 404). The Markdown
    file already written under `data/` is left alone: the audit trail is
    append-only, and `/report/{id}/download` is the export path.
    """
    with tenant_scope(tenant):
        deleted = await delete_job_async(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="job not found")
    return {"deleted": True, "job_id": job_id}


@app.get("/metrics")
async def metrics():
    return Response(
        content=get_metrics_output(),
        media_type="text/plain; version=0.0.4",
    )


@app.post("/webhook/github")
async def github_webhook(request: Request):
    """GitHub App webhook: PR opened -> analyze diff -> comment."""
    return await handle_webhook(request)


class CheckoutRequest(BaseModel):
    email: str
    success_url: str
    cancel_url: str


@app.post("/billing/checkout")
async def checkout(req: CheckoutRequest):
    """Create a Stripe Checkout Session (subscription)."""
    return create_checkout_session(req.email, req.success_url, req.cancel_url)


class InvoiceRequest(BaseModel):
    customer_id: str
    description: str
    amount_cents: int


@app.post("/billing/invoice", dependencies=[Depends(current_user)])
async def create_invoice_endpoint(req: InvoiceRequest):
    """Create a one-off enterprise invoice (Clerk auth required)."""
    if req.amount_cents <= 0:
        raise HTTPException(status_code=400, detail="amount_cents must be positive")
    return create_invoice(req.customer_id, req.description, req.amount_cents)


@app.get("/billing/products")
async def billing_products():
    """Active Stripe prices, or an empty list when Stripe is not configured."""
    return list_prices()


@app.get("/api/me/data")
async def export_my_data(user: dict = Depends(current_user)):
    """GDPR: export every record stored for the caller's tenant."""
    with tenant_scope(user["tenant_id"]):
        return await export_user_data(user["tenant_id"])


@app.delete("/api/me")
async def delete_my_account(user: dict = Depends(current_user)):
    """GDPR: erase every record stored for the caller's tenant."""
    with tenant_scope(user["tenant_id"]):
        return await delete_user_data(user["tenant_id"])


@app.get("/auth/sso/login")
async def sso_login(tenant: str = Query(..., description="Tenant/org id requesting SSO")):
    """SAML SSO login (stub: requires Clerk Enterprise plan)."""
    return await saml_login(tenant)


@app.post("/auth/sso/callback")
async def sso_callback(payload: dict):
    """SAML assertion callback (stub: requires Clerk Enterprise plan)."""
    return await saml_callback(payload)


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook: verify signature, handle subscription events."""
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    return await handle_stripe_webhook_async(payload, sig)


@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
@traced("analyze")
async def analyze(req: AnalyzeRequest):
    """
    Р В РІР‚вЂќР В Р’В°Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р В РЎвЂќР В Р’В°Р В Р’ВµР РЋРІР‚С™ Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ pipeline Vishap V5.9.
    
    Р В РІР‚в„ўР РЋРІР‚В¦Р В РЎвЂўР В РўвЂ: Р В РЎвЂќР В РЎвЂўР В РўвЂ / spec / logs.
    Р В РІР‚в„ўР РЋРІР‚в„–Р РЋРІР‚В¦Р В РЎвЂўР В РўвЂ: Р РЋРІР‚С›Р В РЎвЂР В Р вЂ¦Р В Р’В°Р В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ Markdown-Р В РЎвЂўР РЋРІР‚С™Р РЋРІР‚РЋР РЋРІР‚ВР РЋРІР‚С™ + Р В РЎВР В Р’ВµР РЋРІР‚С™Р В Р’В°Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ.
    """
    if not req.material.strip():
        raise HTTPException(status_code=400, detail="material Р В Р вЂ¦Р В Р’Вµ Р В РЎВР В РЎвЂўР В Р’В¶Р В Р’ВµР РЋРІР‚С™ Р В Р’В±Р РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„–Р В РЎВ")

    # === Idempotency: check if same material already analyzed ===
    from src.pipeline.orchestrator import compute_hash
    from src.storage.history import find_done_by_hash

    material_hash = compute_hash(req.material)
    existing = None if getattr(req, 'force', False) else find_done_by_hash(material_hash)

    if existing:
        cached_session = existing.get("session_id", "")
        result_file = DATA_DIR / f"result_{cached_session}.json"
        if result_file.exists():
            cached = json.loads(result_file.read_text(encoding="utf-8"))
            stage0c = cached.get("stage0", {})
            stage1c = cached.get("stage1", {})
            stage2c = cached.get("stage2", {})
            tokens_in_c = sum(s.get("_meta", {}).get("tokens_in", 0) for s in [stage0c, stage1c, stage2c])
            tokens_out_c = sum(s.get("_meta", {}).get("tokens_out", 0) for s in [stage0c, stage1c, stage2c])
            return AnalyzeResponse(
                session_id=cached.get("session_id", cached_session),
                filename=cached.get("filename", req.filename),
                level=stage0c.get("level"),
                route=stage0c.get("route"),
                final_markdown=cached.get("final_markdown", ""),
                timestamp=cached.get("timestamp", ""),
                tokens_in=tokens_in_c,
                tokens_out=tokens_out_c,
                cost_usd=cached.get("cost_usd", 0.0),
                audit=cached.get("audit", {}),
                completeness=cached.get("completeness", {}),
                material_hash_full=cached.get("audit", {}).get("material_hash_full", cached.get("material_hash", "")),
                truncated=cached.get("audit", {}).get("truncated", False),
                original_size=cached.get("audit", {}).get("original_size", 0),
                cached=True,
                audit_id=cached.get("audit", {}).get("audit_id", ""),
                material_hash=cached.get("audit", {}).get("material_hash", ""),
                verdict=cached.get("audit", {}).get("critique_verdict", ""),
                pii_detected=bool(cached.get("audit", {}).get("pii_detected", False)),
                compliance_flags=cached.get("audit", {}).get("compliance_flags", []),
            )

    try:
        from src.pipeline.orchestrator import run_pipeline_async
        result = await run_pipeline_async(
            material=req.material,
            filename=req.filename,
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    stage0 = result.get("stage0", {})
    stage1 = result.get("stage1", {})
    stage2 = result.get("stage2", {})

    tokens_in = sum(
        s.get("_meta", {}).get("tokens_in", 0)
        for s in [stage0, stage1, stage2]
    )
    tokens_out = sum(
        s.get("_meta", {}).get("tokens_out", 0)
        for s in [stage0, stage1, stage2]
    )
    from src.pipeline.cost import sum_stage_costs
    stage3 = result.get("stage3") or {}
    stage4 = result.get("stage4") or {}
    cost_usd = sum_stage_costs([stage0, stage1, stage2, stage3, stage4])

    _audit = result.get("audit", {}) or {}
    return AnalyzeResponse(
        session_id=result["session_id"],
        filename=result["filename"],
        level=stage0.get("level"),
        route=stage0.get("route"),
        final_markdown=result["final_markdown"],
        timestamp=result["timestamp"],
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        audit_id=_audit.get("audit_id", ""),
        material_hash=_audit.get("material_hash", ""),
        verdict=_audit.get("critique_verdict", ""),
        material_hash_full=_audit.get("material_hash_full", ""),
        truncated=_audit.get("truncated", False),
        original_size=_audit.get("original_size", 0),
        pii_detected=bool(_audit.get("pii_detected", False)),
        compliance_flags=_audit.get("compliance_flags", []),
        audit=result.get("audit", {}),
        completeness=result.get("completeness", {}),
    )


@app.post("/analyze/secure", dependencies=[Depends(current_user)])
async def analyze_secure(req: AnalyzeRequest, user: dict = Depends(current_user)):
    """Analyze with Clerk JWT auth (multi-tenant); /analyze keeps API-key auth."""
    with tenant_scope(user["tenant_id"]):
        return await analyze(req)


@app.post("/analyze/batch", response_model=BatchResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze_batch(req: BatchRequest):
    """
    Р В РЎСџР В Р’В°Р РЋР вЂљР В Р’В°Р В Р’В»Р В Р’В»Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ Р В Р’В°Р В Р вЂ¦Р В Р’В°Р В Р’В»Р В РЎвЂР В Р’В· Р РЋР С“Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В РЎвЂќР В Р’В° Р В РЎВР В Р’В°Р РЋРІР‚С™Р В Р’ВµР РЋР вЂљР В РЎвЂР В Р’В°Р В Р’В»Р В РЎвЂўР В Р вЂ .

    Р В РІР‚в„ўР РЋРІР‚В¦Р В РЎвЂўР В РўвЂ: Р РЋР С“Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В РЎвЂўР В РЎвЂќ {material, filename}.
    Р В РІР‚в„ўР РЋРІР‚в„–Р РЋРІР‚В¦Р В РЎвЂўР В РўвЂ: Р РЋР С“Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В РЎвЂўР В РЎвЂќ Р РЋР вЂљР В Р’ВµР В Р’В·Р РЋРЎвЂњР В Р’В»Р РЋР Р‰Р РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В РЎвЂўР В Р вЂ  Р В Р вЂ  Р РЋРІР‚С™Р В РЎвЂўР В РЎВ Р В Р’В¶Р В Р’Вµ Р В РЎвЂ”Р В РЎвЂўР РЋР вЂљР РЋР РЏР В РўвЂР В РЎвЂќР В Р’Вµ.

    max_concurrent: 1..10 (Р В РЎвЂ”Р В РЎвЂў Р РЋРЎвЂњР В РЎВР В РЎвЂўР В Р’В»Р РЋРІР‚РЋР В Р’В°Р В Р вЂ¦Р В РЎвЂР РЋР вЂ№ 3). Р В РІР‚ВР В РЎвЂўР В Р’В»Р РЋР Р‰Р РЋРІвЂљВ¬Р В Р’Вµ 10 Р Р†Р вЂљРІР‚Сњ Р РЋР вЂљР В РЎвЂР РЋР С“Р В РЎвЂќ harness overload.
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="items Р В Р вЂ¦Р В Р’Вµ Р В РЎВР В РЎвЂўР В Р’В¶Р В Р’ВµР РЋРІР‚С™ Р В Р’В±Р РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„–Р В РЎВ")

    for i, item in enumerate(req.items):
        if not item.material.strip():
            raise HTTPException(
                status_code=400,
                detail=f"items[{i}].material Р В Р вЂ¦Р В Р’Вµ Р В РЎВР В РЎвЂўР В Р’В¶Р В Р’ВµР РЋРІР‚С™ Р В Р’В±Р РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„–Р В РЎВ",
            )

    materials = [(item.material, item.filename) for item in req.items]

    try:
        results = run_batch(
            materials,
            max_concurrent=req.max_concurrent,
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch error: {str(e)}")

    response_items = []
    for r, item in zip(results, req.items):
        if r is None or "error" in r:
            response_items.append(BatchResponseItem(
                filename=item.filename,
                error=(r or {}).get("error", "unknown"),
            ))
            continue

        stage0 = r.get("stage0", {}) or {}
        audit = r.get("audit", {}) or {}

        response_items.append(BatchResponseItem(
            session_id=r.get("session_id"),
            filename=item.filename,
            level=stage0.get("level"),
            route=stage0.get("route"),
            final_markdown=r.get("final_markdown"),
            verdict=audit.get("critique_verdict"),
            pii_detected=audit.get("pii_detected"),
        ))

    return BatchResponse(
        results=response_items,
        count=len(response_items),
        max_concurrent=req.max_concurrent,
    )


@app.post("/analyze/sarif", dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze_sarif(req: AnalyzeRequest):
    """Run analysis and return SARIF 2.1.0 JSON (for GitHub Code Scanning)."""
    result = await analyze(req)

    audit = result.audit.model_dump() if hasattr(result, "audit") else {}

    # Extract SAST/SCA from audit if present (dict)
    sast_result = None
    sca_result = None
    if isinstance(audit, dict):
        sast_tools = audit.get("sast_tools", {})
        if sast_tools:
            sast_result = {
                "total_findings": audit.get("sast_findings", 0),
                "high_priority": audit.get("sast_high_priority", 0),
                "bandit": {"available": True, "summary": sast_tools.get("bandit", {}), "findings": []},
                "semgrep": {"available": True, "summary": sast_tools.get("semgrep", {}), "findings": []},
            }

    sarif = to_sarif(
        audit=audit if isinstance(audit, dict) else {},
        sast_result=sast_result,
        sca_result=sca_result,
        source_file=req.filename,
    )
    return JSONResponse(content=sarif)


@app.get("/history", response_model=list[HistoryItem])
async def history(limit: int = 20, tenant: str = Depends(current_tenant)):
    """Р В РІР‚в„ўР В РЎвЂўР В Р’В·Р В Р вЂ Р РЋР вЂљР В Р’В°Р РЋРІР‚В°Р В Р’В°Р В Р’ВµР РЋРІР‚С™ Р В РЎвЂ”Р В РЎвЂўР РЋР С“Р В Р’В»Р В Р’ВµР В РўвЂР В Р вЂ¦Р В РЎвЂР В Р’Вµ N Р В Р’В·Р В Р’В°Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В Р’ВµР В РІвЂћвЂ“ Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋРЎвЂњР РЋРІР‚В°Р В Р’ВµР В РЎвЂ“Р В РЎвЂў tenant."""
    with tenant_scope(tenant):
        items = load_history(tenant_id=tenant)
        return [
            HistoryItem(
                session_id=item.get("session_id", ""),
                filename=item.get("filename", ""),
                level=item.get("level"),
                route=item.get("route"),
                material_size=item.get("material_size", 0),
                timestamp=item.get("timestamp", ""),
                verdict=item.get("verdict"),
                pii_detected=item.get("pii_detected"),
            )
            for item in items[-limit:]
        ]


@app.post("/history/clear", dependencies=[Depends(verify_api_key), Depends(rate_limit_read)])
async def history_clear(tenant: str = Depends(current_tenant)):
    """Р В РЎвЂєР РЋРІР‚РЋР В РЎвЂР РЋРІР‚В°Р В Р’В°Р В Р’ВµР РЋРІР‚С™ Р В РЎвЂР РЋР С“Р РЋРІР‚С™Р В РЎвЂўР РЋР вЂљР В РЎвЂР РЋР вЂ№ Р РЋРІР‚С™Р В РЎвЂўР В Р’В»Р РЋР Р‰Р В РЎвЂќР В РЎвЂў Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋРЎвЂњР РЋРІР‚В°Р В Р’ВµР В РЎвЂ“Р В РЎвЂў tenant."""
    from src.storage.history import clear_history

    with tenant_scope(tenant):
        removed = clear_history(tenant_id=tenant)
    return {"status": "ok", "removed": removed}


@app.get("/audit/export", dependencies=[Depends(verify_api_key), Depends(rate_limit_read)])
async def audit_export(
    format: Literal["csv", "json"] = "csv",
    from_date: str | None = Query(None, alias="from", description="ISO 8601 lower bound"),
    to_date: str | None = Query(None, alias="to", description="ISO 8601 upper bound"),
    status: Literal["queued", "running", "done", "failed"] | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    tenant: str = Depends(current_tenant),
):
    """Р В Р’В­Р В РЎвЂќР РЋР С“Р В РЎвЂ”Р В РЎвЂўР РЋР вЂљР РЋРІР‚С™ audit trail Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋРЎвЂњР РЋРІР‚В°Р В Р’ВµР В РЎвЂ“Р В РЎвЂў tenant Р В Р вЂ  CSV Р В РЎвЂР В Р’В»Р В РЎвЂ JSON."""
    with tenant_scope(tenant):
        return await export_audit(
            format=format,
            from_date=from_date,
            to_date=to_date,
            status=status,
            limit=limit,
        )


# ============================================================
# v6.0: Async API -- job-based analysis
# ============================================================

async def _run_job_async(job_id: str, req: "AnalyzeRequest", tenant: str):
    """Run pipeline in background, update job store."""
    from src.pipeline.orchestrator import run_pipeline_async
    with tenant_scope(tenant):
        await update_job_async(
            job_id, status="running", started_at=datetime.now(UTC).isoformat()
        )
        try:
            result = await run_pipeline_async(
                material=req.material,
                filename=req.filename or "unknown",
                verbose=False,
            )
            await update_job_async(
                job_id,
                status="done",
                result=result,
                finished_at=datetime.now(UTC).isoformat(),
            )
            # Downloadable copy; fail-open so a disk problem cannot fail the job.
            save_report(job_id, (result or {}).get("final_markdown"))
            await notify_webhook(
                "job.completed", {"job_id": job_id, "tenant_id": tenant, "status": "done"}
            )
        except Exception as e:
            await update_job_async(
                job_id,
                status="failed",
                error=str(e),
                finished_at=datetime.now(UTC).isoformat(),
            )
            await notify_webhook(
                "job.failed",
                {"job_id": job_id, "tenant_id": tenant, "status": "failed", "error": str(e)},
            )


@app.post("/analyze/async", dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
@traced("analyze_async")
async def analyze_async(req: "AnalyzeRequest", background: BackgroundTasks,
                        tenant: str = Depends(current_tenant)):
    """Create async job -- returns job_id immediately."""
    with tenant_scope(tenant):
        job_id = await create_job_async(
            filename=req.filename or "unknown", tenant_id=tenant
        )
        await notify_webhook(
            "job.queued",
            {
                "job_id": job_id,
                "tenant_id": tenant,
                "filename": req.filename or "unknown",
                "status": "queued",
            },
        )
        if broker_available():
            run_analysis_task.delay(job_id, req.material, req.filename or "unknown", tenant)
        else:
            # v6.1: broker unavailable -> in-process fallback (graceful degradation)
            log.warning("celery_broker_unavailable", job_id=job_id)
            background.add_task(_run_job_async, job_id, req, tenant)
        return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def get_status(job_id: str, tenant: str = Depends(current_tenant)):
    """Get job status."""
    with tenant_scope(tenant):
        job = await get_job_async(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "filename": job["filename"],
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "finished_at": job["finished_at"],
            "error": job["error"],
        }


@app.get("/report/{job_id}")
async def get_report(job_id: str, tenant: str = Depends(current_tenant)):
    """Get job result. 409 if not done."""
    with tenant_scope(tenant):
        job = await get_job_async(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job["status"] != "done":
            raise HTTPException(
                status_code=409,
                detail=f"job not done: {job['status']}",
            )
        return job["result"]


@app.get("/report/{job_id}/download")
async def download_report(job_id: str, tenant: str = Depends(current_tenant)):
    """Download the Markdown report of a finished job.

    Two sources, in order: the `.md` file on disk, then `final_markdown` inside
    the job result. The second one matters because the file is written by
    whatever process ran the pipeline РІР‚вЂќ with a Celery worker that is a different
    process, possibly on a different host with a different data directory.
    Serving from the job result means a finished job is always downloadable, and
    the missing file simply gets repaired for next time.
    """
    with tenant_scope(tenant):
        job = await get_job_async(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")

        try:
            path = report_path(job_id)
        except InvalidReportPath:
            path = None

        if path is not None and path.exists():
            return FileResponse(
                path,
                media_type="text/markdown",
                filename=f"{job_id}.md",
            )

        markdown = (job.get("result") or {}).get("final_markdown")
        if markdown:
            if path is not None:
                # Repair the on-disk copy; fail-open, the response does not wait on it.
                save_report(job_id, markdown)
            return Response(
                content=markdown,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{job_id}.md"'},
            )

        raise HTTPException(status_code=404, detail="report not found")


# CORS РІР‚вЂќ applied as an explicit outer wrap so it also covers error responses.
#
# Loopback UIs only: Next dev (:3000), the Tauri desktop shell
# (`http://tauri.localhost` / `tauri://localhost`), plus any loopback port via the
# regex. `allow_private_network` answers the Private Network Access preflight the
# desktop webview sends (its origin is the public address space, `127.0.0.1` is
# local) РІР‚вЂќ see the notes in the CORS comment at the top.
#
# `app` stays the FastAPI instance (tests import it directly); `cors_app` is what
# the server actually runs. The outer wrap is what puts `Access-Control-Allow-Origin`
# on unhandled-500 responses too РІР‚вЂќ a bare 500 from ServerErrorMiddleware would
# otherwise have no CORS header and the webview would report "blocked by CORS".
cors_app = CORSMiddleware(
    app,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
    ],
    allow_origin_regex=(
        r"^(https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?"
        r"|tauri://localhost|https?://tauri\.localhost)$"
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    allow_private_network=True,
)


if __name__ == "__main__":
    import uvicorn
    # Dogfood P0 fix: if no API key set, bind only to 127.0.0.1.
    host = "0.0.0.0" if is_auth_enabled() else "127.0.0.1"
    print(f"[Auth] API key {'set' if is_auth_enabled() else 'NOT set'} -- binding to {host}")
    uvicorn.run(
        cors_app,
        host=host,
        port=PORT,
        reload=False,
    )





