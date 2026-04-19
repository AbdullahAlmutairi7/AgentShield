import os
import uuid

import httpx


BASE = "http://127.0.0.1:8787"


def post_json(url: str, payload: dict) -> httpx.Response:
    return httpx.post(url, json=payload, timeout=120.0)


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY first.")

    session_id = f"step14-quarantine-{uuid.uuid4()}"

    # First request should pass
    payload = {
        "session_id": session_id,
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "Say hello in one sentence."}
                ]
            }
        ]
    }

    print("\n--- FIRST REQUEST (before quarantine) ---")
    response1 = httpx.post(
        f"{BASE}/v1beta/models/gemini-2.5-flash-lite:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120.0,
    )
    print("STATUS:", response1.status_code)
    print(response1.text[:800])

    # Quarantine the session via operator API
    print("\n--- QUARANTINE SESSION ---")
    q = post_json(f"{BASE}/api/operator/session/{session_id}/quarantine", {})
    print("STATUS:", q.status_code)
    print(q.text[:800])

    # Second request should now be blocked
    print("\n--- SECOND REQUEST (after quarantine) ---")
    response2 = httpx.post(
        f"{BASE}/v1beta/models/gemini-2.5-flash-lite:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120.0,
    )
    print("STATUS:", response2.status_code)
    print(response2.text[:800])


if __name__ == "__main__":
    main()
