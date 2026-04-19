from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from agentshield.api.dashboard_service import (
    get_dashboard_alerts,
    get_dashboard_recent_events,
    get_dashboard_session_detail,
    get_dashboard_sessions,
    get_dashboard_summary,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def write_json(filename: str, payload: dict | list) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return str(path)


def write_csv(filename: str, rows: list[dict]) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename

    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("")
        return str(path)

    fieldnames = sorted(set().union(*(row.keys() for row in rows)))

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return str(path)


def generate_dashboard_summary_report() -> dict:
    stamp = now_stamp()
    summary = get_dashboard_summary()

    json_path = write_json(f"dashboard_summary_{stamp}.json", summary)

    return {
        "report_type": "dashboard_summary",
        "generated_at": stamp,
        "json_path": json_path,
    }


def generate_recent_events_export(limit: int = 200) -> dict:
    stamp = now_stamp()
    events = get_dashboard_recent_events(limit=limit)

    json_path = write_json(f"recent_events_{stamp}.json", events)
    csv_path = write_csv(f"recent_events_{stamp}.csv", events)

    return {
        "report_type": "recent_events",
        "generated_at": stamp,
        "count": len(events),
        "json_path": json_path,
        "csv_path": csv_path,
    }


def generate_alerts_export(limit: int = 200) -> dict:
    stamp = now_stamp()
    alerts = get_dashboard_alerts(limit=limit)

    json_path = write_json(f"alerts_{stamp}.json", alerts)
    csv_path = write_csv(f"alerts_{stamp}.csv", alerts)

    return {
        "report_type": "alerts",
        "generated_at": stamp,
        "count": len(alerts),
        "json_path": json_path,
        "csv_path": csv_path,
    }


def generate_sessions_export(limit: int = 200) -> dict:
    stamp = now_stamp()
    sessions = get_dashboard_sessions(limit=limit)

    json_path = write_json(f"sessions_{stamp}.json", sessions)
    csv_path = write_csv(f"sessions_{stamp}.csv", sessions)

    return {
        "report_type": "sessions",
        "generated_at": stamp,
        "count": len(sessions),
        "json_path": json_path,
        "csv_path": csv_path,
    }


def generate_session_incident_report(session_id: str) -> dict:
    stamp = now_stamp()
    detail = get_dashboard_session_detail(session_id)

    safe_session_id = session_id.replace("/", "_").replace(":", "_")
    json_path = write_json(f"incident_{safe_session_id}_{stamp}.json", detail)

    event_rows = detail.get("events", [])
    csv_path = write_csv(f"incident_{safe_session_id}_{stamp}.csv", event_rows)

    return {
        "report_type": "session_incident",
        "generated_at": stamp,
        "session_id": session_id,
        "event_count": len(event_rows),
        "json_path": json_path,
        "csv_path": csv_path,
    }
