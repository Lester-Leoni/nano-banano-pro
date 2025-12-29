from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SubscriptionTier(str, Enum):
    """Future subscription tiers.

    IMPORTANT: This is a *label* only; it MUST NOT be treated as an entitlement
    decision source without a verified backend.
    """

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class UserIdentity:
    """Identity for interactive UI sessions.

    Today there is no auth, so the default is anonymous.
    """

    user_id: str
    email: Optional[str] = None
    is_authenticated: bool = False


@dataclass(frozen=True)
class ApiClientIdentity:
    """Identity for future programmatic API clients.

    key_id is a non-secret identifier used for lookups/analytics.
    The actual API key material must never be stored here.
    """

    client_id: str
    key_id: str = ""
    display_name: str = ""
