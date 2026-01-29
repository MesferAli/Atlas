"""Secrets management with Alibaba Cloud KMS support.

In production (ATLAS_KMS_ENABLED=true), fetches secrets from Alibaba Cloud
KMS. Otherwise falls back to environment variables (dev/CI).

Usage:
    from atlas.api.security.secrets import get_secret
    db_password = get_secret("ORACLE_PASSWORD")
"""

import json
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

# KMS configuration
KMS_ENABLED = os.getenv("ATLAS_KMS_ENABLED", "false").lower() == "true"
KMS_REGION = os.getenv("ATLAS_KMS_REGION", "cn-riyadh")
KMS_SECRET_NAME = os.getenv("ATLAS_KMS_SECRET_NAME", "atlas/production")


class SecretsManager:
    """Centralized secrets manager with KMS backend and local fallback."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()
        self._kms_client: Any = None

    def _init_kms(self) -> Any:
        """Lazily initialize the Alibaba Cloud KMS client."""
        if self._kms_client is not None:
            return self._kms_client

        try:
            from alibabacloud_kms_kms20160120.client import Client
            from alibabacloud_tea_openapi.models import Config

            config = Config(
                access_key_id=os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
                access_key_secret=os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
                region_id=KMS_REGION,
            )
            self._kms_client = Client(config)
            return self._kms_client
        except ImportError:
            logger.warning(
                "Alibaba Cloud KMS SDK not installed. "
                "Install with: pip install alibabacloud-kms-kms20160120"
            )
            return None
        except KeyError as e:
            logger.warning("KMS credentials not set: %s", e)
            return None

    def _fetch_from_kms(self, key: str) -> str | None:
        """Fetch a secret value from Alibaba Cloud KMS Secrets Manager."""
        client = self._init_kms()
        if client is None:
            return None

        try:
            from alibabacloud_kms_kms20160120.models import (
                GetSecretValueRequest,
            )

            request = GetSecretValueRequest(
                secret_name=KMS_SECRET_NAME,
                version_stage="ACSCurrent",
            )
            response = client.get_secret_value(request)
            secret_data = json.loads(response.body.secret_data)
            return secret_data.get(key)
        except Exception as e:
            logger.error("KMS fetch failed for %s: %s", key, e)
            return None

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get a secret by key. Checks cache → KMS → env vars."""
        # Check cache first
        with self._lock:
            if key in self._cache:
                return self._cache[key]

        value = None

        # Try KMS if enabled
        if KMS_ENABLED:
            value = self._fetch_from_kms(key)
            if value is not None:
                with self._lock:
                    self._cache[key] = value
                return value

        # Fallback to environment variable
        value = os.getenv(key, default)
        if value is not None:
            with self._lock:
                self._cache[key] = value

        return value

    def clear_cache(self) -> None:
        """Clear the secrets cache (e.g., on rotation)."""
        with self._lock:
            self._cache.clear()


# Singleton
_manager = SecretsManager()


def get_secret(key: str, default: str | None = None) -> str | None:
    """Fetch a secret from KMS or environment variables."""
    return _manager.get(key, default)


def clear_secrets_cache() -> None:
    """Clear cached secrets (call after rotation)."""
    _manager.clear_cache()
