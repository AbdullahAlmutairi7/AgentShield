from __future__ import annotations

import time
from typing import Any

import psutil

from agentshield.core.events import EventType, Severity, make_host_event
from agentshield.detectors.risk_engine import score_event_risk
from agentshield.storage.events_repo import save_event


class ProcessCollector:
    def __init__(self) -> None:
        self.seen_pids: set[int] = set()

    def poll(self) -> int:
        count = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline", "username"]):
            try:
                pid = proc.info["pid"]
                if pid in self.seen_pids:
                    continue

                self.seen_pids.add(pid)
                name = proc.info.get("name") or "unknown"
                cmdline = " ".join(proc.info.get("cmdline") or [])
                username = proc.info.get("username") or "unknown"

                event = make_host_event(
                    session_id="host-process-monitor",
                    event_type=EventType.PROCESS_EVENT,
                    action="process.spawn",
                    summary=f"Observed process: {name}",
                    pid=pid,
                    severity=Severity.INFO,
                    reason=f"user={username} cmd={cmdline[:300]}",
                )
                event.agent_id = "host"
                event.agent_name = "Linux Process Collector"
                event.raw_payload = {
                    "name": name,
                    "cmdline": cmdline,
                    "username": username,
                }

                lowered = f"{name} {cmdline}".lower()
                if any(x in lowered for x in ["ssh", "scp", "curl", "wget", "nc", "bash -c"]):
                    event.severity = Severity.MEDIUM

                score_event_risk(event)
                save_event(event)
                count += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return count
