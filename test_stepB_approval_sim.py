import os
import uuid

import httpx


BASE = "http://127.0.0.1:8787"


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY first.")

    session_id = f"stepb-approval-{uuid.uuid4()}"

    payload = {
        "session_id": session_id,
        "tools": [
            {"name": "exec", "description": "Run shell command"}
        ],
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Use the tool to inspect the current directory."}],
            }
        ]
    }

    response = httpx.post(
        f"{BASE}/v1beta/models/gemini-2.5-flash-lite:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120.0,
    )

    print("STATUS:", response.status_code)
    print(response.text[:1200])


if __name__ == "__main__":
    main()
