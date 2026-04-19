from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agentshield.core.events import EventType, Severity, make_host_event
from agentshield.detectors.risk_engine import score_event_risk
from agentshield.storage.events_repo import save_event


WATCH_PATHS = [
    str(Path.home() / ".ssh"),
    str(Path.home() / ".aws"),
    str(Path.home() / ".gnupg"),
    str(Path.home() / "Downloads"),
    str(Path.home() / "Documents"),
]

IGNORED_PATH_PARTS = [
    "agentshield.db",
    "agentshield.db-wal",
    "agentshield.db-shm",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
]

ALLOWED_EVENT_TYPES = {"created", "modified", "deleted", "moved"}


class FileEventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.last_seen: dict[str, float] = {}
        self.debounce_seconds = 2.0

    def _should_ignore(self, path: str, event_type: str, is_directory: bool) -> bool:
        lowered = path.lower()

        if is_directory:
            return True

        if event_type not in ALLOWED_EVENT_TYPES:
            return True

        if any(part.lower() in lowered for part in IGNORED_PATH_PARTS):
            return True

        now = time.time()
        key = f"{event_type}:{path}"
        last = self.last_seen.get(key, 0.0)

        if now - last < self.debounce_seconds:
            return True

        self.last_seen[key] = now
        return False

    def on_any_event(self, event) -> None:
        path = getattr(event, "src_path", None)
        if not path:
            return

        is_directory = getattr(event, "is_directory", False)
        event_type = getattr(event, "event_type", "unknown")

        if self._should_ignore(path, event_type, is_directory):
            return

        action = f"file.{event_type}"
        summary = f"Observed file event: {event_type}"

        host_event = make_host_event(
            session_id="host-file-monitor",
            event_type=EventType.FILE_EVENT,
            action=action,
            summary=summary,
            path=path,
            severity=Severity.LOW,
            reason=f"file event type={event_type}",
        )
        host_event.agent_id = "host"
        host_event.agent_name = "Linux File Collector"
        host_event.raw_payload = {
            "path": path,
            "event_type": event_type,
            "is_directory": is_directory,
        }

        lowered = path.lower()
        if any(x in lowered for x in [".ssh", ".aws", ".gnupg", "id_rsa", ".pem", "credentials"]):
            host_event.severity = Severity.HIGH

        score_event_risk(host_event)
        save_event(host_event)


class FileCollector:
    def __init__(self) -> None:
        self.observer = Observer()
        self.handler = FileEventHandler()

    def start(self) -> None:
        for path in WATCH_PATHS:
            p = Path(path)
            if p.exists():
                self.observer.schedule(self.handler, path, recursive=True)
        self.observer.start()

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join()
