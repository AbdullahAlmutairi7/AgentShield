from __future__ import annotations

from agentshield.config.settings import load_settings
from agentshield.core.events import EventType, Severity, make_host_event
from agentshield.storage.db import init_db
from agentshield.storage.events_repo import save_event


def bootstrap() -> dict:
    settings = load_settings()
    init_db()

    startup_event = make_host_event(
        session_id="system-bootstrap",
        event_type=EventType.STATUS_EVENT,
        action="system.bootstrap",
        summary="AgentShield bootstrap completed",
        severity=Severity.INFO,
        reason=f"Mode={settings.app.mode}, Policy={settings.policy.mode}, Provider={settings.proxy.upstream_provider}, Model={settings.proxy.default_model}",
    )

    save_event(startup_event)

    return {
        "app_name": settings.app.name,
        "version": settings.app.version,
        "mode": settings.app.mode,
        "policy_mode": settings.policy.mode,
        "proxy": f"{settings.proxy.host}:{settings.proxy.port}",
        "ui": f"{settings.ui.host}:{settings.ui.port}",
        "provider": settings.proxy.upstream_provider,
        "model": settings.proxy.default_model,
    }
