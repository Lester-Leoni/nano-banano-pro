import os
import json
import base64
import hashlib
import ipaddress
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import urlparse, urljoin
import logging
import socket
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple


logger = logging.getLogger(__name__)


def get_api_config() -> Dict[str, Any]:
    """Читает конфиг API из переменных окружения.

    Переменные:
      - NANOBANANO_API_URL (например: https://example.com/api)
      - NANOBANANO_API_KEY (опционально)
      - NANOBANANO_TIMEOUT (сек), по умолчанию 30
    """
    api_url_raw = (os.getenv("NANOBANANO_API_URL") or "").strip().rstrip("/")
    api_url = _validate_base_url(api_url_raw)

    return {
        "api_url": api_url,
        "api_key": (os.getenv("NANOBANANO_API_KEY") or "").strip(),
        "timeout": int(os.getenv("NANOBANANO_TIMEOUT") or "30"),
    }


def _is_private_host(host: str) -> bool:
    """SSRF guard.

    Блокируем:
      - localhost / *.localhost / *.local
      - прямые IP-адреса из private/loopback/link-local/reserved диапазонов
      - домены, которые DNS-резолвятся (A/AAAA) в любой private/loopback/link-local IP

    Fail-safe: если DNS-резолв не удался, считаем хост небезопасным.
    """
    h = (host or "").strip().lower()
    if not h:
        return True
    if h in {"localhost", "localhost."}:
        return True
    if h.endswith(".localhost") or h.endswith(".local"):
        return True

    def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:  # type: ignore[attr-defined]
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )

    # Если это IP-адрес — блокируем private/loopback/link-local и т.п.
    try:
        ip = ipaddress.ip_address(h)
        return _is_blocked_ip(ip)
    except ValueError:
        pass

    # Если это домен — делаем DNS resolve и блокируем, если *любой* IP небезопасен.
    try:
        infos = socket.getaddrinfo(h, None, type=socket.SOCK_STREAM)
    except OSError:
        return True

    resolved: set[str] = set()
    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET:
            resolved.add(sockaddr[0])
        elif family == socket.AF_INET6:
            resolved.add(sockaddr[0])

    if not resolved:
        return True

    for ip_str in resolved:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _is_blocked_ip(ip_obj):
            return True

    return False


def _validate_base_url(base_url: str) -> str:
    """Строгая валидация базового URL API.

    - По умолчанию разрешаем только https
      (http допускается только если NANOBANANO_ALLOW_INSECURE_HTTP=1)
    - Запрещаем пустой host
    - Запрещаем локальные/приватные хосты (SSRF guard)
    """
    base_url = (base_url or "").strip().rstrip("/")
    if not base_url:
        return ""

    parsed = urllib.parse.urlparse(base_url)
    allow_http = os.getenv("NANOBANANO_ALLOW_INSECURE_HTTP", "").strip().lower() in {"1", "true", "yes"}
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("NANOBANANO_API_URL: разрешены только https (и http только при NANOBANANO_ALLOW_INSECURE_HTTP=1)")
    if parsed.scheme == "http" and not allow_http:
        raise ValueError("NANOBANANO_API_URL: http запрещён по умолчанию (включи NANOBANANO_ALLOW_INSECURE_HTTP=1 если осознанно)")
    if parsed.username or parsed.password:
        raise ValueError("NANOBANANO_API_URL: userinfo в URL запрещён")
    if not parsed.hostname:
        raise ValueError("NANOBANANO_API_URL: отсутствует hostname")
    if _is_private_host(parsed.hostname):
        raise ValueError("NANOBANANO_API_URL: запрещён локальный/приватный host")

    # Нормализуем (без лишнего / на конце)
    return urllib.parse.urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",
            "",
            "",
        )
    )


def _read_bytes(uploaded_file) -> bytes:
    """Streamlit UploadedFile обычно имеет getvalue(); поддержим и read()."""
    if uploaded_file is None:
        return b""
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue() or b""
    if hasattr(uploaded_file, "read"):
        return uploaded_file.read() or b""
    return b""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def _b64(data: bytes) -> str:
    return base64.b64encode(data or b"").decode("utf-8")


def _file_meta(file_obj, include_bytes: bool = False, max_inline_bytes: int = 2_000_000) -> Dict[str, Any]:
    data = _read_bytes(file_obj)
    name = getattr(file_obj, "name", "file")
    out: Dict[str, Any] = {
        "name": name,
        "size": len(data),
        "sha256": _sha256(data),
        "inline_included": False,
    }
    if include_bytes and len(data) <= max_inline_bytes:
        out["base64"] = _b64(data)
        out["inline_included"] = True
    return out


def _is_url(s: str) -> bool:
    s = (s or "").strip().lower()
    return s.startswith(("http://", "https://", "www."))


def normalize_refs(image_urls: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Нормализует ссылки/описания: {var: [ {kind: url|text, value: ...} ] }"""
    out: Dict[str, List[Dict[str, Any]]] = {}
    for var, items in (image_urls or {}).items():
        lst: List[Dict[str, Any]] = []
        for raw in (items or []):
            v = (raw or "").strip()
            if not v:
                continue
            lst.append({"kind": "url" if _is_url(v) else "text", "value": v})
        if lst:
            out[var] = lst
    return out


@dataclass
class NanoBananoAPIClient:
    api_url: str
    api_key: str = ""
    timeout: int = 30

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.api_url.rstrip("/") + (path if path.startswith("/") else "/" + path)

        allow_http = os.getenv("NANOBANANO_ALLOW_INSECURE_HTTP", "").strip().lower() in {"1", "true", "yes"}

        def _validate_request_url(u: str) -> None:
            # Validate immediately before any network I/O (best-effort DNS rebinding mitigation).
            parsed = urlparse(u)
            if parsed.scheme not in {"https", "http"}:
                raise RuntimeError("Invalid API URL scheme")
            if parsed.scheme == "http" and not allow_http:
                raise RuntimeError("Insecure http is not allowed")
            if parsed.username or parsed.password:
                raise RuntimeError("Invalid API URL userinfo")
            host = parsed.hostname
            if not host:
                raise RuntimeError("Invalid API URL host")
            if _is_private_host(host):
                raise RuntimeError("Blocked private/loopback API host")

        # Disable automatic redirects and re-validate each redirect target.
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
                return None

        opener = urllib.request.build_opener(_NoRedirect())

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        method: str = "POST"
        body: Optional[bytes] = data
        headers = self._headers()

        current_url = url
        max_redirects = 5
        try:
            for _ in range(max_redirects + 1):
                req = urllib.request.Request(current_url, data=body, headers=headers, method=method)
                try:
                    # Validate immediately before any network I/O (best-effort DNS rebinding mitigation).
                    _validate_request_url(current_url)
                    with opener.open(req, timeout=self.timeout) as resp:
                        raw = resp.read().decode("utf-8", errors="ignore")
                        try:
                            return json.loads(raw) if raw else {"ok": True}
                        except Exception:
                            return {"ok": True, "raw": raw}
                except urllib.error.HTTPError as e:
                    # Handle redirects safely (validate each target before following).
                    code = getattr(e, "code", None)
                    if code in {301, 302, 303, 307, 308}:
                        location = (e.headers.get("Location") or "").strip()
                        if not location:
                            raise
                        next_url = urljoin(current_url, location)
                        _validate_request_url(next_url)

                        # Emulate urllib redirect semantics for POST.
                        if code in {301, 302, 303} and method != "HEAD":
                            method = "GET"
                            body = None
                        current_url = next_url
                        continue
                    raise
            raise RuntimeError("API request failed (too many redirects).")
        except urllib.error.HTTPError as e:
            status = getattr(e, "code", None)
            reason = getattr(e, "reason", "")
            body_len = 0
            try:
                raw = e.read() or b""
                body_len = len(raw)
            except Exception:
                body_len = 0
            logger.warning(
                "API request failed: HTTP %s %s url=%s body_len=%s",
                status,
                reason,
                url,
                body_len,
            )
            raise RuntimeError(f"API request failed (HTTP {status}).")
        except urllib.error.URLError as e:
            logger.warning("API request failed: network error url=%s err=%r", url, e)
            raise RuntimeError("API request failed (network error).")


# -----------------------------
# Payload builders
# -----------------------------
def build_api_payload_v2(
    *,
    prompt_id: str,
    title: str,
    category: str,
    ru_prompt: str,
    en_prompt: str,
    negative_ru: str = "",
    negative_en: str = "",
    uploaded_files: Optional[Dict[str, Any]] = None,
    image_urls: Optional[Dict[str, List[str]]] = None,
    include_file_bytes: bool = False,
    max_inline_bytes: int = 2_000_000,
) -> Dict[str, Any]:
    """Новый payload (для будущего API).

    include_file_bytes: добавляет base64 только если файл <= max_inline_bytes
    """
    uploaded_files = uploaded_files or {}
    image_urls = image_urls or {}

    files_out: Dict[str, List[Dict[str, Any]]] = {}
    for var, files in uploaded_files.items():
        if files is None:
            continue
        if not isinstance(files, list):
            files = [files]
        metas = [_file_meta(f, include_bytes=include_file_bytes, max_inline_bytes=max_inline_bytes) for f in files if f]
        if metas:
            files_out[var] = metas

    payload: Dict[str, Any] = {
        "meta": {
            "prompt_id": prompt_id,
            "title": title,
            "category": category,
        },
        "prompts": {
            "ru": ru_prompt,
            "en": en_prompt,
            "negative_ru": negative_ru,
            "negative_en": negative_en,
        },
        "refs": normalize_refs(image_urls),
        "files": files_out,
    }
    return payload


def build_api_payload(*args, **kwargs) -> Dict[str, Any]:
    """Legacy + V2 совместимость.

    Старый вызов:
        build_api_payload(task_id, prompt, negative_prompt, inputs, uploaded_files=..., image_urls=..., include_file_bytes=False)

    Новый вызов (keyword-only):
        build_api_payload(prompt_id=..., title=..., category=..., ru_prompt=..., en_prompt=..., ...)
    """
    if kwargs.get("prompt_id"):
        return build_api_payload_v2(**kwargs)

    # legacy mode
    if len(args) < 4:
        raise TypeError("build_api_payload legacy expects (task_id, prompt, negative_prompt, inputs, ...)")
    task_id, prompt, negative_prompt, inputs = args[0], args[1], args[2], args[3]
    uploaded_files = kwargs.get("uploaded_files")
    image_urls = kwargs.get("image_urls")
    include_file_bytes = bool(kwargs.get("include_file_bytes", False))

    # Map legacy into v2
    return build_api_payload_v2(
        prompt_id=str(task_id),
        title=str(task_id),
        category="",
        ru_prompt=str(prompt),
        en_prompt=str(prompt),
        negative_ru=str(negative_prompt),
        negative_en=str(negative_prompt),
        uploaded_files=uploaded_files,
        image_urls=image_urls,
        include_file_bytes=include_file_bytes,
    )
