# -*- coding: utf-8 -*-
"""Clerk JWT verification via JWKS (v6.1)."""
import os
from typing import Any

import httpx
import jwt


class AuthError(Exception):
    """Raised when a Clerk JWT cannot be verified."""


_jwks_cache: dict[str, Any] = {}


def is_configured() -> bool:
    """True when Clerk can verify tokens (a JWKS URL is available).

    ``CLERK_SECRET_KEY`` alone is not enough to verify an RS256 token — the
    public keys come from the JWKS document. Endpoints that depend on
    :func:`verify_jwt` therefore answer 401 with "Clerk not configured" rather
    than failing with a 500 when the deployment has no Clerk credentials.
    """
    return bool(os.getenv("CLERK_JWKS_URL", "").strip())


def _fetch_jwks() -> dict:
    """Fetch (and cache) the Clerk JWKS document."""
    url = os.getenv("CLERK_JWKS_URL", "").strip()
    if not url:
        raise AuthError("Clerk not configured")
    if url not in _jwks_cache:
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        _jwks_cache[url] = r.json()
    return _jwks_cache[url]


def verify_jwt(token: str) -> dict:
    """Verify a Clerk RS256 JWT against JWKS; return its claims."""
    if not is_configured():
        raise AuthError("Clerk not configured")

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise AuthError("No kid in token header")

        jwks = _fetch_jwks()
        key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_data:
            raise AuthError(f"Unknown kid: {kid}")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        claims = jwt.decode(token, public_key, algorithms=["RS256"])

        if "sub" not in claims:
            raise AuthError("Missing 'sub' claim")
        return claims
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidSignatureError:
        raise AuthError("Invalid signature")
    except jwt.PyJWTError as e:
        raise AuthError(f"JWT error: {e}")
