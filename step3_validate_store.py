from pprint import pprint

from agentshield.storage.query_service import (
    get_alert_feed,
    get_event_counts,
    get_recent_events,
    get_session_summaries,
)


def main() -> None:
    print("\n=== EVENT COUNTS ===")
    pprint(get_event_counts())

    print("\n=== RECENT EVENTS ===")
    for event in get_recent_events(limit=5):
        pprint(event)

    print("\n=== SESSION SUMMARIES ===")
    for session in get_session_summaries():
        pprint(session)

    print("\n=== ALERT FEED ===")
    for alert in get_alert_feed(limit=10):
        pprint(alert)


if __name__ == "__main__":
    main()
