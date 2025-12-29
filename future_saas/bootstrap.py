from __future__ import annotations

import uuid

import streamlit as st

from .auth import NoAuthProvider
from .config import FutureSaaSConfig, UsageMode, load_future_config
from .context import RequestContext
from .usage import NoopUsageRecorder, UsageRecorder


@st.cache_resource
def get_future_config() -> FutureSaaSConfig:
    return load_future_config()


@st.cache_resource
def get_usage_recorder() -> UsageRecorder:
    cfg = get_future_config()
    # Only NOOP is implemented today.
    if cfg.usage_mode != UsageMode.NOOP:
        return NoopUsageRecorder()
    return NoopUsageRecorder()


def _ensure_session_id() -> str:
    sid = st.session_state.get("_nb_session_id")
    if isinstance(sid, str) and sid:
        return sid
    sid = uuid.uuid4().hex
    st.session_state["_nb_session_id"] = sid
    return sid


def _get_ip_and_ua(*, trust_proxy_headers: bool) -> tuple[str, str]:
    # Streamlit does not provide a stable official public API for request headers.
    # Keep placeholders for future integration via gateway/reverse proxy.
    _ = trust_proxy_headers
    return ("", "")


def get_request_context() -> RequestContext:
    """Build a safe RequestContext for the current interaction."""

    cfg = get_future_config()
    session_id = _ensure_session_id()
    request_id = uuid.uuid4().hex
    ip, ua = _get_ip_and_ua(trust_proxy_headers=cfg.trust_proxy_headers)

    # Current state: no auth. Future: swap provider based on cfg.auth_mode.
    provider = NoAuthProvider()
    return provider.get_context(request_id=request_id, session_id=session_id, ip=ip, user_agent=ua)
