from __future__ import annotations

from typing import Any


def extract_response_preview(response_json: dict[str, Any]) -> str:
    candidates = response_json.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return ""

    first = candidates[0]
    if not isinstance(first, dict):
        return ""

    content = first.get("content", {})
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts", [])
    if not isinstance(parts, list):
        return ""

    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())

    return " ".join(texts)[:500]


def extract_usage_stats(response_json: dict[str, Any]) -> dict[str, int]:
    usage = response_json.get("usageMetadata", {})
    if not isinstance(usage, dict):
        return {
            "prompt_tokens": 0,
            "candidate_tokens": 0,
            "total_tokens": 0,
        }

    return {
        "prompt_tokens": int(usage.get("promptTokenCount", 0) or 0),
        "candidate_tokens": int(usage.get("candidatesTokenCount", 0) or 0),
        "total_tokens": int(usage.get("totalTokenCount", 0) or 0),
    }
