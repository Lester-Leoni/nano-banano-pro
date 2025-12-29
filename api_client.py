import os
import json
import base64
import hashlib
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple


def get_api_config() -> Dict[str, Any]:
    """Читает конфиг API из переменных окружения.

    Переменные:
      - NANOBANANO_API_URL (например: https://example.com/api)
      - NANOBANANO_API_KEY (опционально)
      - NANOBANANO_TIMEOUT (сек), по умолчанию 30
    """
    return {
        "api_url": (os.getenv("NANOBANANO_API_URL") or "").strip().rstrip("/"),
        "api_key": (os.getenv("NANOBANANO_API_KEY") or "").strip(),
        "timeout": int(os.getenv("NANOBANANO_TIMEOUT") or "30"),
    }


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
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                try:
                    return json.loads(raw) if raw else {"ok": True}
                except Exception:
                    return {"ok": True, "raw": raw}
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code}: {body or e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e}")


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
