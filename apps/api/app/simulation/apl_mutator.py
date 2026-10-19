from __future__ import annotations

import re

# TCI keys that must never come from user-controlled custom APL / profile text.
FORBIDDEN_KEYS = {
    "threads",
    "html",
    "xml",
    "json",
    "json2",
    "output",
    "save",
    "armory",
    "guild",
    "wowhead",
    "local_json",
    "proxy",
    "report_details",
    "hosted_html",
    "input",
    "ptr",
    "copy",
}

ALLOWED_CUSTOM_PREFIXES = (
    "actions",
    "skip_actions",
    "default_actions",
)


_TOKEN_RE = re.compile(r"^[a-z0-9_/\.\-]+$", re.IGNORECASE)


def sanitize_skip_actions(actions: list[str]) -> str | None:
    cleaned: list[str] = []
    for action in actions:
        token = action.strip().lower().replace(" ", "_")
        if not token:
            continue
        if not _TOKEN_RE.match(token) or "/" in token:
            # Disallow path-like or multi tokens inside a single entry
            if not re.fullmatch(r"[a-z0-9_]+", token):
                raise ValueError(f"Invalid skip_actions token: {action}")
        cleaned.append(token)
    if not cleaned:
        return None
    # Unique, stable order
    seen: set[str] = set()
    ordered: list[str] = []
    for token in cleaned:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return "/".join(ordered)


def validate_custom_apl(apl_text: str) -> list[str]:
    """Return sanitized APL lines. Raises ValueError on forbidden content."""
    if not apl_text or not apl_text.strip():
        return []

    lines: list[str] = []
    for raw in apl_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if any(ch in line for ch in (";", "`", "$(", "&&", "||", ">", "<")):
            raise ValueError("Custom APL contains forbidden shell-like characters")
        if "=" not in line:
            raise ValueError(f"Custom APL line must be key=value: {line}")
        key = line.split("=", 1)[0].strip().lower()
        base = key.split(".", 1)[0]
        if base in FORBIDDEN_KEYS or key in FORBIDDEN_KEYS:
            raise ValueError(f"Forbidden SimC option in custom APL: {key}")
        if not any(key == p or key.startswith(p + ".") or key.startswith(p + "+") for p in ALLOWED_CUSTOM_PREFIXES):
            if not key.startswith("actions"):
                raise ValueError(f"Only actions*/skip_actions allowed in custom APL, got: {key}")
        lines.append(line)
    return lines


def build_priority_apl(priority: list[str]) -> list[str]:
    """Build a minimal custom APL from an ordered list of allowlisted action tokens."""
    actions = [a.strip().lower().replace(" ", "_") for a in priority if a.strip()]
    for action in actions:
        if not re.fullmatch(r"[a-z0-9_]+", action):
            raise ValueError(f"Invalid priority action token: {action}")
    if not actions:
        return []
    lines = ["actions=auto_attack"]
    for action in actions:
        if action == "auto_attack":
            continue
        lines.append(f"actions+=/{action}")
    return lines
