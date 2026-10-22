# -*- coding: utf-8 -*-
"""Pre-LLM PII/secrets redaction.

Dogfood finding (P0): PII and secrets were sent to the cloud LLM
before being detected. Detection ran only in run_audit() AFTER all
stages. This module redacts PII/secrets BEFORE any LLM call.

Uses the same regex patterns as orchestrator.PII_PATTERNS to keep
detection and redaction in sync.
"""
from src.tools.patterns import PII_PATTERNS


# Placeholder per PII category
PLACEHOLDERS = {
    "email": "<EMAIL_REDACTED>",
    "phone_ru": "<PHONE_REDACTED>",
    "passport_ru": "<PASSPORT_REDACTED>",
    "snils": "<SNILS_REDACTED>",
    "iban": "<IBAN_REDACTED>",
    "aws_access_key": "<AWS_ACCESS_KEY_REDACTED>",
    "aws_secret_key": "<AWS_SECRET_KEY_REDACTED>",
    "stripe_live_key": "<STRIPE_LIVE_KEY_REDACTED>",
    "stripe_test_key": "<STRIPE_TEST_KEY_REDACTED>",
    "github_token": "<GITHUB_TOKEN_REDACTED>",
    "slack_token": "<SLACK_TOKEN_REDACTED>",
    "google_api_key": "<GOOGLE_API_KEY_REDACTED>",
    "private_key": "<PRIVATE_KEY_REDACTED>",
    "hardcoded_password": "<PASSWORD_REDACTED>",
    "hardcoded_secret": "<SECRET_REDACTED>",
}


def redact_pii(text: str) -> tuple[str, dict]:
    """Replace PII/secrets with placeholders.

    Args:
        text: material text (may contain PII/secrets)

    Returns:
        (redacted_text, mapping) where mapping = {category: count}

    Note: this function is idempotent — running it twice is safe.
    """
    if not text:
        return text, {}

    redacted = text
    mapping = {}

    for name, pattern in PII_PATTERNS.items():
        placeholder = PLACEHOLDERS.get(name, "<{}_REDACTED>".format(name.upper()))
        matches = pattern.findall(redacted)
        if matches:
            mapping[name] = len(matches)
            redacted = pattern.sub(placeholder, redacted)

    return redacted, mapping


def is_redacted(text: str) -> bool:
    """Check if text contains any redaction placeholders."""
    return "<" in text and "_REDACTED>" in text
