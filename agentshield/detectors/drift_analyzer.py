from __future__ import annotations

import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def jaccard_similarity(a: str, b: str) -> float:
    a_tokens = set(tokenize(a))
    b_tokens = set(tokenize(b))

    if not a_tokens and not b_tokens:
        return 1.0
    if not a_tokens or not b_tokens:
        return 0.0

    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def keyword_overlap(anchor_goal: str, current_text: str) -> float:
    a = Counter(tokenize(anchor_goal))
    b = Counter(tokenize(current_text))

    if not a or not b:
        return 0.0

    shared = sum((a & b).values())
    total = sum(a.values())
    if total == 0:
        return 0.0
    return shared / total


def compute_drift_score(anchor_goal: str | None, current_text: str | None) -> float:
    if not anchor_goal or not current_text:
        return 0.0

    similarity = jaccard_similarity(anchor_goal, current_text)
    overlap = keyword_overlap(anchor_goal, current_text)

    drift = 1.0 - ((similarity + overlap) / 2.0)
    return round(max(0.0, min(1.0, drift)), 4)
