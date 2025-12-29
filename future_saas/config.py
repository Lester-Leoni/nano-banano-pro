from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class AuthMode(str, Enum):
    """Auth strategy.

    NOTE: Only NONE is implemented today.
    """

    NONE = "none"
    # Future modes (design placeholders):
    API_KEY = "api_key"  # per-client key in header
    PROXY_JWT = "proxy_jwt"  # verified upstream (reverse proxy / gateway)


class SecretsMode(str, Enum):
    """Where secrets come from.

    NOTE: Only ENV is used today.
    """

    ENV = "env"
    # Future modes (design placeholders):
    VAULT = "vault"
    AWS_SM = "aws_sm"
    GCP_SM = "gcp_sm"
    AZURE_KV = "azure_kv"


class UsageMode(str, Enum):
    """Usage accounting backend.

    NOTE: Only NOOP is implemented today.
    """

    NOOP = "noop"
    # Future modes (design placeholders):
    LOG = "log"
    REDIS = "redis"
    HTTP = "http"


def _env_int(name: str, default: int) -> int:
    try:
        raw = (os.getenv(name) or "").strip()
        return int(raw) if raw else int(default)
    except Exception:
        return int(default)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class FutureSaaSConfig:
    """Configuration knobs for future SaaS hardening.

    All values are safe-by-default. Most toggles are *inactive* until you wire a
    real auth/usage layer.
    """

    auth_mode: AuthMode = AuthMode.NONE
    secrets_mode: SecretsMode = SecretsMode.ENV
    usage_mode: UsageMode = UsageMode.NOOP

    # If enabled, show exception details in UI. Default is OFF (safe).
    debug_errors: bool = False

    # Future: if you deploy behind a trusted reverse proxy, you may want to trust
    # X-Forwarded-* headers for IP/user-agent attribution.
    trust_proxy_headers: bool = False

    # Future: request-level soft limits (placeholders)
    usage_units_per_minute: int = 0  # 0 => unlimited (no enforcement)

    # Header names (future API-key auth)
    api_key_header: str = "X-API-Key"
    api_key_id_header: str = "X-API-Key-Id"


def load_future_config() -> FutureSaaSConfig:
    auth_raw = (os.getenv("NANOBANANO_AUTH_MODE") or "none").strip().lower()
    secrets_raw = (os.getenv("NANOBANANO_SECRETS_MODE") or "env").strip().lower()
    usage_raw = (os.getenv("NANOBANANO_USAGE_MODE") or "noop").strip().lower()

    def _as_enum(raw: str, enum_cls, default):
        try:
            return enum_cls(raw)
        except Exception:
            return default

    return FutureSaaSConfig(
        auth_mode=_as_enum(auth_raw, AuthMode, AuthMode.NONE),
        secrets_mode=_as_enum(secrets_raw, SecretsMode, SecretsMode.ENV),
        usage_mode=_as_enum(usage_raw, UsageMode, UsageMode.NOOP),
        debug_errors=_env_bool("NANOBANANO_DEBUG_ERRORS", False),
        trust_proxy_headers=_env_bool("NANOBANANO_TRUST_PROXY_HEADERS", False),
        usage_units_per_minute=_env_int("NANOBANANO_USAGE_UNITS_PER_MINUTE", 0),
        api_key_header=(os.getenv("NANOBANANO_API_KEY_HEADER") or "X-API-Key").strip(),
        api_key_id_header=(os.getenv("NANOBANANO_API_KEY_ID_HEADER") or "X-API-Key-Id").strip(),
    )
