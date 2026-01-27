"""
Webhook Signature Verification for Atlas API

SECURITY: VERIFY SIGNATURES - NEVER trust webhook payloads directly.
- All webhooks MUST be cryptographically verified
- Failed verification returns 400 immediately
- Timestamps are checked to prevent replay attacks
"""

import hashlib
import hmac
import os
import time
from typing import Any


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: int | None = None,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify a webhook signature using HMAC-SHA256.

    SECURITY:
    - Uses constant-time comparison to prevent timing attacks
    - Validates timestamp to prevent replay attacks
    - Returns False on any verification failure

    Args:
        payload: Raw request body as bytes
        signature: Signature from webhook header
        secret: Webhook signing secret
        timestamp: Unix timestamp from webhook header (optional)
        tolerance_seconds: Maximum age of webhook in seconds

    Returns:
        True if signature is valid, False otherwise

    Raises:
        WebhookVerificationError: If verification fails with details
    """
    # Check timestamp to prevent replay attacks
    if timestamp is not None:
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance_seconds:
            raise WebhookVerificationError(
                f"Webhook timestamp too old or in the future. "
                f"Current: {current_time}, Received: {timestamp}"
            )

    # Compute expected signature
    if timestamp is not None:
        # Include timestamp in signature (Stripe-style)
        signed_payload = f"{timestamp}.".encode() + payload
    else:
        signed_payload = payload

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    if not hmac.compare_digest(signature, expected_signature):
        raise WebhookVerificationError("Invalid webhook signature")

    return True


def verify_stripe_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> dict[str, Any]:
    """
    Verify a Stripe webhook signature.

    SECURITY: Follows Stripe's signature verification protocol.
    https://stripe.com/docs/webhooks/signatures

    Args:
        payload: Raw request body
        signature_header: Stripe-Signature header value
        secret: Webhook signing secret (whsec_...)
        tolerance_seconds: Maximum age of webhook

    Returns:
        Parsed webhook payload as dict

    Raises:
        WebhookVerificationError: If verification fails
    """
    import json

    # Parse Stripe signature header
    # Format: t=timestamp,v1=signature,v0=signature(deprecated)
    elements = {}
    for part in signature_header.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            elements[key] = value

    timestamp_str = elements.get("t")
    signature = elements.get("v1")

    if not timestamp_str or not signature:
        raise WebhookVerificationError(
            "Invalid Stripe signature header format"
        )

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        raise WebhookVerificationError("Invalid timestamp in signature header")

    # Verify the signature
    signed_payload = f"{timestamp}.".encode() + payload
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise WebhookVerificationError("Invalid Stripe webhook signature")

    # Check timestamp
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance_seconds:
        raise WebhookVerificationError("Stripe webhook timestamp outside tolerance")

    # Parse and return payload
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise WebhookVerificationError(f"Invalid JSON payload: {e}")


def verify_lemonsqueezy_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> dict[str, Any]:
    """
    Verify a LemonSqueezy webhook signature.

    SECURITY: Follows LemonSqueezy's signature verification protocol.

    Args:
        payload: Raw request body
        signature_header: X-Signature header value
        secret: Webhook signing secret

    Returns:
        Parsed webhook payload as dict

    Raises:
        WebhookVerificationError: If verification fails
    """
    import json

    # LemonSqueezy uses HMAC-SHA256 with hex encoding
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature_header, expected_signature):
        raise WebhookVerificationError("Invalid LemonSqueezy webhook signature")

    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise WebhookVerificationError(f"Invalid JSON payload: {e}")


class WebhookHandler:
    """
    Generic webhook handler with signature verification.

    SECURITY: Provides a consistent interface for handling webhooks
    with proper signature verification.

    Usage:
        handler = WebhookHandler(secret="whsec_...")

        @app.post("/webhooks/stripe")
        async def stripe_webhook(request: Request):
            payload = await request.body()
            signature = request.headers.get("Stripe-Signature", "")

            try:
                data = handler.verify_and_parse(payload, signature, "stripe")
                # Process webhook...
            except WebhookVerificationError as e:
                return Response(status_code=e.status_code, content=e.message)
    """

    def __init__(
        self,
        stripe_secret: str | None = None,
        lemonsqueezy_secret: str | None = None,
        generic_secret: str | None = None,
    ):
        self.secrets = {
            "stripe": stripe_secret or os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            "lemonsqueezy": lemonsqueezy_secret or os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", ""),
            "generic": generic_secret or os.getenv("WEBHOOK_SECRET", ""),
        }

    def verify_and_parse(
        self,
        payload: bytes,
        signature: str,
        provider: str = "generic",
    ) -> dict[str, Any]:
        """
        Verify and parse a webhook payload.

        Args:
            payload: Raw request body
            signature: Signature header value
            provider: Webhook provider (stripe, lemonsqueezy, generic)

        Returns:
            Parsed webhook payload

        Raises:
            WebhookVerificationError: If verification fails
        """
        secret = self.secrets.get(provider)
        if not secret:
            raise WebhookVerificationError(
                f"No secret configured for provider: {provider}"
            )

        if provider == "stripe":
            return verify_stripe_signature(payload, signature, secret)
        elif provider == "lemonsqueezy":
            return verify_lemonsqueezy_signature(payload, signature, secret)
        else:
            # Generic verification
            import json

            verify_webhook_signature(payload, signature, secret)
            return json.loads(payload.decode("utf-8"))
