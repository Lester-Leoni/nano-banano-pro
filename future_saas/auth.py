from __future__ import annotations

from abc import ABC, abstractmethod

from .context import RequestContext
from .identity import SubscriptionTier, UserIdentity


class AuthProvider(ABC):
    """Produces a RequestContext with identity information.

    Only NoAuthProvider is implemented today.
    """

    @abstractmethod
    def get_context(self, *, request_id: str, session_id: str, ip: str, user_agent: str) -> RequestContext:
        raise NotImplementedError


class NoAuthProvider(AuthProvider):
    """Anonymous access (current state)."""

    def get_context(self, *, request_id: str, session_id: str, ip: str, user_agent: str) -> RequestContext:
        return RequestContext(
            request_id=request_id,
            session_id=session_id,
            ip=ip,
            user_agent=user_agent,
            user=UserIdentity(user_id="anonymous", is_authenticated=False),
            api_client=None,
            tier=SubscriptionTier.FREE,
        )
