from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .identity import ApiClientIdentity, SubscriptionTier, UserIdentity


@dataclass(frozen=True)
class RequestContext:
    """Per-request context, safe to attach to logs/usage accounting.

    DO NOT include secrets or user-provided content in this structure.
    """

    request_id: str
    session_id: str
    ip: str = ""
    user_agent: str = ""

    user: Optional[UserIdentity] = None
    api_client: Optional[ApiClientIdentity] = None
    tier: SubscriptionTier = SubscriptionTier.FREE
