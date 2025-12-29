from __future__ import annotations

"""Safe error handling for a future SaaS posture.

Goal: avoid leaking secrets and internals to untrusted clients.
"""


def public_error_message(exc: Exception, *, debug: bool = False) -> str:
    """Return a user-facing error message.

    If debug=True (local dev), include the exception string.
    """

    if debug:
        return f"❌ Ошибка: {exc}"
    return "❌ Ошибка при генерации. Попробуйте снова."
