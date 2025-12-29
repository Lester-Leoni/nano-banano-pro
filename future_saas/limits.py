from __future__ import annotations

"""Usage limit hooks.

This module exists to make adding:
  - per-user/API key limits
  - tiered quotas
  - burst controls

possible without rewriting the app.

Current implementation is allow-all.
"""

from .context import RequestContext
from .usage import UsageAction


def enforce_usage_limits(ctx: RequestContext, action: UsageAction, units: int = 1) -> bool:
    """Return True if the action is allowed.

    Future design:
    - consult a quota backend
    - implement replay/burst protection
    - deny-by-default for unknown tiers in SaaS mode

    Today: always allow.
    """

    _ = (ctx, action, units)
    return True
