from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

SENSITIVE_KEYS = ("auth", "token", "secret", "key", "cookie", "password")


def validate_json_text(text: str) -> Tuple[bool, Optional[str]]:
    """Validate JSON text. Empty string is treated as valid (no body).

    Returns (ok, error_message).
    """
    if not text or not text.strip():
        return True, None
    try:
        json.loads(text)
        return True, None
    except Exception as e:  # pragma: no cover - message content not critical
        return False, str(e)


def mask_headers(headers: Dict[str, str] | None) -> Dict[str, str]:
    """Return a masked copy of headers values for sensitive keys.

    Keys containing SENSITIVE_KEYS (case-insensitive) will have value replaced with '***'.
    """
    masked: Dict[str, str] = {}
    for k, v in (headers or {}).items():
        if any(tok in k.lower() for tok in SENSITIVE_KEYS):
            masked[k] = "***"
        else:
            masked[k] = v
    return masked


def build_full_url(base_url: str, path: str, query: Dict[str, object] | None) -> str:
    path = path if path.startswith("/") else f"/{path}"
    # Ensure base has no trailing slash duplication
    base = base_url.rstrip("/")
    # Cast query values to str and allow lists via doseq
    if query:
        q_items: Dict[str, object] = {}
        for k, v in query.items():
            if isinstance(v, (list, tuple)):
                q_items[k] = [str(x) for x in v]
            else:
                q_items[k] = str(v)
        q = f"?{urlencode(q_items, doseq=True)}"
    else:
        q = ""
    return f"{base}{path}{q}"


def _config_dir() -> Path:
    # Allow override for tests
    override = os.environ.get("IMAGE_SAVER_CONFIG_DIR")
    if override:
        return Path(override)
    home = Path(os.environ.get("HOME", str(Path.cwd())))
    return home.joinpath(".image-saver")


def _config_path() -> Path:
    return _config_dir().joinpath("ui_config.json")


def load_config() -> Dict:
    p = _config_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg: Dict) -> None:
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = _config_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def summarize_response(status: int, duration_ms: int, text: str, content_type: Optional[str]) -> Dict:
    ct_lower = content_type.lower() if content_type else ""
    if "json" in ct_lower:
        body_type = "json"
    elif "text" in ct_lower or "html" in ct_lower:
        body_type = "text"
    else:
        body_type = "other"
    preview_limit = 8000
    preview = text if len(text) <= preview_limit else text[:preview_limit] + "\n... (truncated)"
    return {
        "status": status,
        "duration_ms": duration_ms,
        "body_type": body_type,
        "body_preview": preview,
    }
