# -*- coding: utf-8 -*-
"""Risk verdict computation -- single source of truth.

Consolidates logic from run_audit() (v5.10.6 risk_nodes, v5.11.1 security.findings).
"""
import re
from typing import Any


# v6.1-fix: fallback scan of final_markdown for critical SEC findings the LLM
# put in free text ([CONCLUSION]) instead of structured security.findings.
_SEC_CRITICAL_RE = re.compile(
    r"SEC-\d+.{0,300}?(критично|critical|CVE-\d|crash|overflow|injection)",
    re.IGNORECASE | re.DOTALL,
)


def _has_critical_priority(items: Any) -> bool:
    """Check if list of dicts has any item with critical priority."""
    if not isinstance(items, list):
        return False
    for item in items:
        if not isinstance(item, dict):
            continue
        prio = str(item.get("priority", "")).lower()
        if prio in ("критично", "critical"):
            return True
    return False


def _has_critical_risk_nodes(stage2_result: dict | None) -> bool:
    """Check stage2.risk_nodes for critical nodes."""
    if not stage2_result:
        return False
    return _has_critical_priority(stage2_result.get("risk_nodes", []))


def _has_critical_security(stage2_result: dict | None) -> bool:
    """Check stage2.security.findings for critical findings."""
    if not stage2_result:
        return False
    sec = stage2_result.get("security", {})
    if not isinstance(sec, dict):
        return False
    return _has_critical_priority(sec.get("findings", []))


def _has_critical_threat_model(stage2_result: dict | None) -> bool:
    """Check stage2.threat_model.threats for critical STRIDE threats."""
    if not stage2_result:
        return False
    tm = stage2_result.get("threat_model", {})
    if not isinstance(tm, dict):
        return False
    return _has_critical_priority(tm.get("threats", []))


def _has_critical_sec_in_text(final_markdown: str) -> bool:
    """Fallback: scan final_markdown text for critical SEC findings."""
    if not final_markdown:
        return False
    return bool(_SEC_CRITICAL_RE.search(final_markdown))


def compute_risk_verdict(
    stage2_result: dict | None,
    pii: list,
    compliance: list,
    cwe_ids: list,
    force_emergency: bool = False,
    final_markdown: str = "",
) -> tuple[str, str]:
    """Compute (risk_verdict, critique_verdict) from all signals.

    Priority order (high to low):
      1. force_emergency -> EMERGENCY
      2. pii / compliance / cwe_ids -> REQUIRES_REVIEW
      3. critical risk_nodes -> REQUIRES_REVIEW
      4. critical security.findings -> REQUIRES_REVIEW
      5. critical threat_model.threats -> REQUIRES_REVIEW
      6. critical SEC in final_markdown text -> REQUIRES_REVIEW (fallback)
      7. else -> SAFE
    """
    if force_emergency:
        return "EMERGENCY", "EMERGENCY"

    if pii or compliance or cwe_ids:
        return "REQUIRES_REVIEW", "REQUIRES_REVIEW"

    if _has_critical_risk_nodes(stage2_result):
        return "REQUIRES_REVIEW", "REQUIRES_REVIEW"

    if _has_critical_security(stage2_result):
        return "REQUIRES_REVIEW", "REQUIRES_REVIEW"

    if _has_critical_threat_model(stage2_result):
        return "REQUIRES_REVIEW", "REQUIRES_REVIEW"

    if _has_critical_sec_in_text(final_markdown):
        return "REQUIRES_REVIEW", "REQUIRES_REVIEW"

    return "SAFE", "SAFE"
