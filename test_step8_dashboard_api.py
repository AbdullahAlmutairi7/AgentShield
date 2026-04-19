from pprint import pprint

import httpx


BASE = "http://127.0.0.1:8787"


def main() -> None:
    print("\n=== SUMMARY ===")
    pprint(httpx.get(f"{BASE}/api/dashboard/summary", timeout=30.0).json())

    print("\n=== RECENT EVENTS ===")
    pprint(httpx.get(f"{BASE}/api/dashboard/recent-events?limit=5", timeout=30.0).json())

    print("\n=== SESSIONS ===")
    pprint(httpx.get(f"{BASE}/api/dashboard/sessions?limit=5", timeout=30.0).json())

    print("\n=== ALERTS ===")
    pprint(httpx.get(f"{BASE}/api/dashboard/alerts?limit=5", timeout=30.0).json())


if __name__ == "__main__":
    main()
