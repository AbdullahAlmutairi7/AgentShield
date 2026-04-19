from __future__ import annotations

import psutil

from agentshield.core.events import EventType, Severity, make_host_event
from agentshield.detectors.risk_engine import score_event_risk
from agentshield.storage.events_repo import save_event


class NetworkCollector:
    def __init__(self) -> None:
        self.seen_connections: set[str] = set()

    def poll(self) -> int:
        count = 0

        try:
            conns = psutil.net_connections(kind="inet")
        except Exception:
            return 0

        for conn in conns:
            try:
                if not conn.raddr:
                    continue

                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "unknown"
                key = f"{conn.pid}|{laddr}|{raddr}|{conn.status}"

                if key in self.seen_connections:
                    continue

                self.seen_connections.add(key)

                event = make_host_event(
                    session_id="host-network-monitor",
                    event_type=EventType.NETWORK_EVENT,
                    action="network.connection",
                    summary=f"Observed network connection to {raddr}",
                    pid=conn.pid,
                    domain=conn.raddr.ip if conn.raddr else None,
                    severity=Severity.INFO,
                    reason=f"local={laddr} remote={raddr} status={conn.status}",
                )
                event.agent_id = "host"
                event.agent_name = "Linux Network Collector"
                event.raw_payload = {
                    "local_address": laddr,
                    "remote_address": raddr,
                    "status": conn.status,
                    "pid": conn.pid,
                }

                if conn.raddr and conn.raddr.port in {80, 443, 8080, 8443}:
                    event.severity = Severity.LOW

                if conn.raddr and any(
                    bad in conn.raddr.ip for bad in ["127.0.0.1"]
                ):
                    event.severity = Severity.INFO

                score_event_risk(event)
                save_event(event)
                count += 1

            except Exception:
                continue

        return count
