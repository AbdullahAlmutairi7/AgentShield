from pprint import pprint

import httpx


BASE = "http://127.0.0.1:8787"


def main() -> None:
    print("\n=== DASHBOARD SUMMARY REPORT ===")
    pprint(httpx.post(f"{BASE}/api/reports/dashboard-summary", timeout=30.0).json())

    print("\n=== EVENTS EXPORT ===")
    pprint(httpx.post(f"{BASE}/api/reports/recent-events?limit=50", timeout=30.0).json())

    print("\n=== ALERTS EXPORT ===")
    pprint(httpx.post(f"{BASE}/api/reports/alerts?limit=50", timeout=30.0).json())

    print("\n=== SESSIONS EXPORT ===")
    pprint(httpx.post(f"{BASE}/api/reports/sessions?limit=50", timeout=30.0).json())


if __name__ == "__main__":
    main()
