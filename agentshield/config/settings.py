from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SETTINGS_PATH = BASE_DIR / "configs" / "settings.yaml"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    mode: str
    log_level: str


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str


class ProxyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str
    port: int
    upstream_provider: str
    upstream_base_url: str
    default_model: str


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    default_decision: str


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_monitoring: bool
    file_monitoring: bool
    network_monitoring: bool


class UIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str
    port: int


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppConfig
    database: DatabaseConfig
    proxy: ProxyConfig
    policy: PolicyConfig
    telemetry: TelemetryConfig
    ui: UIConfig


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or SETTINGS_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)
    return Settings(**raw)
