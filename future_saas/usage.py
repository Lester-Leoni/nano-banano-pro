from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from .context import RequestContext


class UsageAction(str, Enum):
    """High-level actions that matter for future billing/limits."""

    GENERATE_PROMPT = "generate_prompt"
    TRANSLATE = "translate"
    DOWNLOAD_RESULT = "download_result"
    COPY_RESULT = "copy_result"


@dataclass(frozen=True)
class UsageEvent:
    """A single accounting record.

    Keep it intentionally metadata-only:
    - no prompt text
    - no raw user inputs
    - no secrets
    """

    action: UsageAction
    ts: float = field(default_factory=lambda: time.time())
    units: int = 1
    request_id: str = ""
    session_id: str = ""
    actor_id: str = ""
    tier: str = ""
    meta: Dict[str, str] = field(default_factory=dict)


class UsageRecorder(ABC):
    """Storage/transport for usage events."""

    @abstractmethod
    def record(self, ctx: RequestContext, event: UsageEvent) -> None:
        raise NotImplementedError

    def flush(self) -> None:  # pragma: no cover
        return None


class NoopUsageRecorder(UsageRecorder):
    def record(self, ctx: RequestContext, event: UsageEvent) -> None:
        return None


def make_event(
    *,
    ctx: RequestContext,
    action: UsageAction,
    units: int = 1,
    meta: Optional[Dict[str, str]] = None,
) -> UsageEvent:
    actor = ""
    if ctx.user and ctx.user.user_id:
        actor = ctx.user.user_id
    elif ctx.api_client and ctx.api_client.client_id:
        actor = ctx.api_client.client_id
    return UsageEvent(
        action=action,
        units=int(units or 1),
        request_id=ctx.request_id,
        session_id=ctx.session_id,
        actor_id=actor,
        tier=str(ctx.tier.value),
        meta=dict(meta or {}),
    )
