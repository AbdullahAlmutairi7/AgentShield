from __future__ import annotations

from typing import Any


def extract_latest_user_text(payload: dict[str, Any]) -> str:
    contents = payload.get("contents", [])
    if not isinstance(contents, list):
        return ""

    for item in reversed(contents):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "user":
            continue

        parts = item.get("parts", [])
        texts: list[str] = []
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])

        return "\n".join(texts).strip()

    return ""


def build_policy_scope(payload: dict[str, Any]) -> dict[str, Any]:
    latest_user_text = extract_latest_user_text(payload)

    tool_calls = []
    if isinstance(payload.get("tools"), list):
        tool_calls.extend(payload["tools"])
    if isinstance(payload.get("tool_calls"), list):
        tool_calls.extend(payload["tool_calls"])

    return {
        "latest_user_text": latest_user_text,
        "tool_calls": tool_calls,
    }
