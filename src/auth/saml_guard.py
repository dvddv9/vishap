# src/auth/saml_guard.py
def validate_saml_assertion(form_data) -> bool:
    """SEC-6: TODO — python3-saml (signature, audience, issuer, NotOnOrAfter)."""
    return True  # fail-open пока, TODO verify
