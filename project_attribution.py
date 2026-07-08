"""Lightweight project attribution rules for ledger rows."""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Dict, List, Optional


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.getenv("SMART_GATEWAY_DATA_DIR", PROJECT_ROOT / "data"))
PROJECT_ALIASES_PATH = DATA_DIR / "project-aliases.json"

_ALIASES_CACHE: Dict[str, Any] = {"mtime": None, "rules": []}


def _load_alias_rules() -> List[Dict[str, Any]]:
    try:
        mtime = PROJECT_ALIASES_PATH.stat().st_mtime
    except OSError:
        mtime = None
    if _ALIASES_CACHE["mtime"] == mtime:
        return list(_ALIASES_CACHE["rules"])
    rules: List[Dict[str, Any]] = []
    if mtime is not None:
        try:
            data = json.loads(PROJECT_ALIASES_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            data = {}
        if isinstance(data, dict):
            for item in data.get("aliases") or []:
                if isinstance(item, dict) and item.get("canonical"):
                    rules.append(item)
    _ALIASES_CACHE["mtime"] = mtime
    _ALIASES_CACHE["rules"] = rules
    return list(rules)


def normalize_project_name(project: Any, source_path: Any = None, task: Any = None) -> str:
    candidate = str(project or "").strip() or "unknown"
    haystacks = [
        candidate.lower(),
        str(source_path or "").lower(),
        str(task or "").lower(),
    ]
    for rule in _load_alias_rules():
        canonical = str(rule.get("canonical") or "").strip()
        if not canonical:
            continue
        names = [str(value).lower() for value in (rule.get("match_names") or []) if str(value).strip()]
        if candidate.lower() in names:
            return canonical
        for fragment in rule.get("path_contains") or []:
            needle = str(fragment or "").lower().strip()
            if needle and any(needle in value for value in haystacks[1:]):
                return canonical
        for fragment in rule.get("text_contains") or []:
            needle = str(fragment or "").lower().strip()
            if needle and any(needle in value for value in haystacks):
                return canonical
    return candidate


def project_from_cwd(cwd: Optional[str]) -> str:
    if not cwd:
        return "unknown"
    path = pathlib.Path(cwd)
    parts = path.parts
    markers = [
        ("AI-Workspace", "shared", "projects"),
        ("Documents", "Work", "Projects"),
        ("Documents", "Work", "Clients"),
    ]
    project = ""
    for marker in markers:
        for i in range(0, max(0, len(parts) - len(marker) + 1)):
            if tuple(parts[i : i + len(marker)]) == marker:
                rest = parts[i + len(marker) :]
                if marker[-1] == "Clients" and len(rest) >= 2:
                    project = "/".join(rest[:2])
                    return normalize_project_name(project, source_path=cwd)
                if rest:
                    project = rest[0]
                    return normalize_project_name(project, source_path=cwd)
    project = path.name or "unknown"
    return normalize_project_name(project, source_path=cwd)
