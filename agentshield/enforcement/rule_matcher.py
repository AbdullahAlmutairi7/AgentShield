from __future__ import annotations

import re
from typing import Any


def find_protected_path_hits(payload: dict[str, Any], protected_paths: list[str]) -> list[str]:
    hits: list[str] = []
    raw = str(payload)

    for path in protected_paths:
        if path in raw:
            hits.append(path)

    return hits


def find_blocked_command_hits(payload: dict[str, Any], blocked_patterns: list[str]) -> list[str]:
    hits: list[str] = []
    raw = str(payload)

    for pattern in blocked_patterns:
        if re.search(pattern, raw, flags=re.IGNORECASE):
            hits.append(pattern)

    return hits


def find_keyword_hits(payload: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    raw = str(payload).lower()

    for keyword in keywords:
        if keyword.lower() in raw:
            hits.append(keyword)

    return hits


def find_tool_hits(payload: dict[str, Any], risky_tools: list[str]) -> list[str]:
    hits: list[str] = []

    tool_calls = []
    if isinstance(payload.get("tools"), list):
        tool_calls.extend(payload["tools"])
    if isinstance(payload.get("tool_calls"), list):
        tool_calls.extend(payload["tool_calls"])

    for tool in tool_calls:
        if not isinstance(tool, dict):
            continue

        name = tool.get("name") or tool.get("function", {}).get("name")
        if isinstance(name, str) and name in risky_tools:
            hits.append(name)

    return hits
    
def find_blocked_domain_hits(payload: dict[str, Any], blocked_domains: list[str]) -> list[str]:
    hits: list[str] = []
    raw = str(payload).lower()

    for domain in blocked_domains:
        if domain.lower() in raw:
            hits.append(domain)

    return hits
