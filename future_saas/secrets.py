from __future__ import annotations

"""Secret handling boundaries (skeleton).

Rules:
 - secrets live in env/vault/secret managers, NOT in code
 - secrets never go to the browser/UI
 - secrets must not be logged

Current implementation supports only env reads.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional


class SecretProvider(ABC):
    @abstractmethod
    def get(self, name: str) -> Optional[str]:
        raise NotImplementedError


class EnvSecretProvider(SecretProvider):
    def get(self, name: str) -> Optional[str]:
        raw = os.getenv(name)
        if raw is None:
            return None
        s = str(raw)
        return s if s.strip() else None


def redact_secret(value: str, *, keep_last: int = 4) -> str:
    """Best-effort redaction for logs.

    Never use this to "make it safe" to log secrets. The correct approach is to
    not log secrets at all. This exists only for future defensive logging.
    """

    if value is None:
        return ""
    s = str(value)
    if len(s) <= keep_last:
        return "***"
    return "***" + s[-keep_last:]
