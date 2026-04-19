from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RULES_PATH = BASE_DIR / "configs" / "enforcement_rules.yaml"


def load_enforcement_rules() -> dict[str, Any]:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
