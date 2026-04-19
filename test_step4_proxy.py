import os
import uuid
import httpx

def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY first.")

    session_id = f"step4-{uuid.uuid4()}"

    payload = {
        "session_id": session_id,
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Say hello in one sentence."}]
            }
        ]
    }

    response = httpx.post(
        "http://127.0.0.1:8787/v1beta/models/gemini-2.5-flash-lite:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120.0,
    )

    print("STATUS:", response.status_code)
    print("BODY:")
    print(response.text)

if __name__ == "__main__":
    main()
