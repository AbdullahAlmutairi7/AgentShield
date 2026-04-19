from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from agentshield.api.dashboard_routes import router as dashboard_router
from agentshield.api.operator_routes import router as operator_router
from agentshield.api.report_routes import router as report_router
from agentshield.config.settings import load_settings
from agentshield.detectors.drift_analyzer import compute_drift_score
from agentshield.enforcement.precheck import run_pre_policy_check
from agentshield.proxy.normalizer import (
    extract_anchor_goal,
    extract_message_count,
    extract_model,
    extract_session_id,
    extract_tool_calls,
    normalize_model_name,
)
from agentshield.proxy.response_parser import extract_response_preview, extract_usage_stats
from agentshield.proxy.runtime_events import (
    emit_drift_alert_event,
    emit_llm_request_event,
    emit_llm_response_event,
    emit_policy_check_event,
    emit_tool_call_event,
)
from agentshield.proxy.sanitizer import split_internal_metadata
from agentshield.proxy.session_store import SessionStore
from agentshield.storage.db import init_db

load_dotenv()

app = FastAPI(title="AgentShield Proxy", version="0.1.0")
app.include_router(dashboard_router)
app.include_router(operator_router)
app.include_router(report_router)

settings = load_settings()
sessions = SessionStore()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "agentshield" / "ui" / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[AgentShield] {request.method} {request.url.path}")
    response = await call_next(request)
    return response


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def dashboard_home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "agentshield-proxy",
        "provider": settings.proxy.upstream_provider,
        "model": settings.proxy.default_model,
    }


@app.get("/sessions")
def list_sessions() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for s in sessions.all_sessions():
        output.append(
            {
                "session_id": s.session_id,
                "agent_id": s.agent_id,
                "agent_name": s.agent_name,
                "provider": s.provider,
                "model": s.model,
                "anchor_goal": s.anchor_goal,
                "message_count": s.message_count,
                "tool_count": s.tool_count,
                "prompt_tokens": s.prompt_tokens,
                "candidate_tokens": s.candidate_tokens,
                "total_tokens": s.total_tokens,
                "created_at": s.created_at.isoformat(),
                "last_seen_at": s.last_seen_at.isoformat(),
            }
        )
    return output


def _normalize_requested_model(model_path: str) -> str:
    value = model_path.strip()
    if value.startswith("models/"):
        value = value[len("models/"):]
    if "/" in value:
        value = value.split("/")[-1]
    return normalize_model_name(value)


def _blocked_json_response(reason: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": 403,
                "message": reason,
                "status": "PERMISSION_DENIED",
            }
        },
    )


def _blocked_sse_response(reason: str) -> Response:
    """
    Return a Gemini-style SSE completion so OpenClaw considers the turn finished
    and does not carry the blocked prompt into the next message.
    """
    payload = {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [
                        {
                            "text": f"Blocked by AgentShield policy: {reason}"
                        }
                    ],
                },
                "finishReason": "STOP",
                "index": 0,
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 0,
            "candidatesTokenCount": 0,
            "totalTokenCount": 0,
        },
    }

    sse_body = f"data: {json.dumps(payload)}\n\n"
    return Response(
        content=sse_body.encode("utf-8"),
        status_code=200,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def _process_for_policy_and_events(
    request: Request,
    model_path: str,
    payload: dict[str, Any],
):
    forward_payload, internal_meta = split_internal_metadata(payload)

    session_id = extract_session_id(payload)
    requested_model = model_path or settings.proxy.default_model
    model = extract_model(payload, default_model=requested_model)
    upstream_model = _normalize_requested_model(model)
    anchor_goal = extract_anchor_goal(payload)
    message_count = extract_message_count(payload)
    tool_calls = extract_tool_calls(payload)

    session = sessions.get_or_create(
        session_id,
        agent_id=internal_meta.get("agent_id", "openclaw"),
        agent_name=internal_meta.get("agent_name", "OpenClaw"),
        provider=settings.proxy.upstream_provider,
        model=model,
    )

    if anchor_goal and not session.anchor_goal:
        sessions.set_anchor_goal(session_id, anchor_goal)

    for _ in range(message_count):
        sessions.increment_message_count(session_id)

    emit_llm_request_event(
        session_id=session_id,
        model=model,
        anchor_goal=anchor_goal or session.anchor_goal,
        payload=forward_payload,
    )

    current_text = anchor_goal or ""
    drift_score = compute_drift_score(session.anchor_goal, current_text)
    if session.anchor_goal and current_text and drift_score >= 0.45:
        emit_drift_alert_event(
            session_id=session_id,
            drift_score=drift_score,
            anchor_goal=session.anchor_goal,
            current_text=current_text,
        )

    for tool in tool_calls:
        tool_name = tool.get("name") or tool.get("function", {}).get("name") or "unknown_tool"
        sessions.increment_tool_count(session_id)
        emit_tool_call_event(
            session_id=session_id,
            tool_name=tool_name,
            tool_payload=tool,
        )

    precheck = run_pre_policy_check(
        session_id=session_id,
        model=model,
        anchor_goal=anchor_goal or session.anchor_goal,
        payload=forward_payload,
    )

    emit_policy_check_event(
        session_id=session_id,
        decision=precheck["decision"],
        blocked=precheck["blocked"],
        reason=precheck["reason"],
        matched_rules=precheck["matched_rules"],
    )

    return forward_payload, upstream_model, model, session_id, precheck


async def _forward_to_gemini(
    upstream_path: str,
    forward_payload: dict[str, Any],
    x_goog_api_key: str | None,
    request: Request,
):
    api_key = x_goog_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing Gemini API key")

    upstream_url = f"{settings.proxy.upstream_base_url}{upstream_path}"

    params = dict(request.query_params)
    params["key"] = api_key

    async with httpx.AsyncClient(timeout=120.0) as client:
        upstream_response = await client.post(
            upstream_url,
            params=params,
            json=forward_payload,
            headers={"Content-Type": "application/json"},
        )

    print(f"[AgentShield] upstream status={upstream_response.status_code}")
    if upstream_response.status_code >= 400:
        print(f"[AgentShield] upstream body={upstream_response.text[:1000]}")

    return upstream_response


def _handle_response_recording(
    session_id: str,
    model: str,
    upstream_response: httpx.Response,
):
    try:
        response_json = upstream_response.json()
    except Exception:
        response_json = {"raw_text": upstream_response.text}

    if isinstance(response_json, dict):
        preview = extract_response_preview(response_json)
        usage = extract_usage_stats(response_json)
        sessions.update_usage(
            session_id,
            prompt_tokens=usage["prompt_tokens"],
            candidate_tokens=usage["candidate_tokens"],
            total_tokens=usage["total_tokens"],
        )
        emit_llm_response_event(
            session_id=session_id,
            model=model,
            response_preview=preview,
        )

    return response_json


@app.post("/v1beta/models/{model_path:path}:generateContent")
async def proxy_generate_content(
    model_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    forward_payload, upstream_model, model, session_id, precheck = await _process_for_policy_and_events(
        request, model_path, payload
    )

    if precheck["blocked"]:
        return _blocked_json_response(precheck["reason"])

    upstream_path = f"/v1beta/models/{upstream_model}:generateContent"
    upstream_response = await _forward_to_gemini(upstream_path, forward_payload, x_goog_api_key, request)
    response_json = _handle_response_recording(session_id, model, upstream_response)

    return JSONResponse(status_code=upstream_response.status_code, content=response_json)


@app.post("/v1beta/models/{model_path:path}:streamGenerateContent")
async def proxy_stream_generate_content(
    model_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    forward_payload, upstream_model, model, session_id, precheck = await _process_for_policy_and_events(
        request, model_path, payload
    )

    if precheck["blocked"]:
        return _blocked_sse_response(precheck["reason"])

    upstream_path = f"/v1beta/models/{upstream_model}:streamGenerateContent"
    upstream_response = await _forward_to_gemini(upstream_path, forward_payload, x_goog_api_key, request)

    if upstream_response.status_code >= 400:
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "application/json"),
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type", "text/event-stream"),
    )


@app.post("/models/{model_path:path}:generateContent")
async def proxy_models_generate_content(
    model_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    forward_payload, upstream_model, model, session_id, precheck = await _process_for_policy_and_events(
        request, model_path, payload
    )

    if precheck["blocked"]:
        return _blocked_json_response(precheck["reason"])

    upstream_path = f"/v1beta/models/{upstream_model}:generateContent"
    upstream_response = await _forward_to_gemini(upstream_path, forward_payload, x_goog_api_key, request)
    response_json = _handle_response_recording(session_id, model, upstream_response)

    return JSONResponse(status_code=upstream_response.status_code, content=response_json)


@app.post("/models/{model_path:path}:streamGenerateContent")
async def proxy_models_stream_generate_content(
    model_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    forward_payload, upstream_model, model, session_id, precheck = await _process_for_policy_and_events(
        request, model_path, payload
    )

    if precheck["blocked"]:
        return _blocked_sse_response(precheck["reason"])

    upstream_path = f"/v1beta/models/{upstream_model}:streamGenerateContent"
    upstream_response = await _forward_to_gemini(upstream_path, forward_payload, x_goog_api_key, request)

    if upstream_response.status_code >= 400:
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "application/json"),
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type", "text/event-stream"),
    )


@app.post("/v1beta/{full_path:path}")
async def proxy_any_v1beta(
    full_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    print(f"[AgentShield] passthrough matched /v1beta/{full_path}")

    forward_payload, _, model, session_id, precheck = await _process_for_policy_and_events(
        request, settings.proxy.default_model, payload
    )

    if precheck["blocked"]:
        if "stream" in full_path.lower():
            return _blocked_sse_response(precheck["reason"])
        return _blocked_json_response(precheck["reason"])

    upstream_response = await _forward_to_gemini(f"/v1beta/{full_path}", forward_payload, x_goog_api_key, request)

    if upstream_response.headers.get("content-type", "").startswith("text/event-stream"):
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "text/event-stream"),
        )

    response_json = _handle_response_recording(session_id, model, upstream_response)
    return JSONResponse(status_code=upstream_response.status_code, content=response_json)


@app.post("/v1/{full_path:path}")
async def proxy_any_v1(
    full_path: str,
    request: Request,
    x_goog_api_key: str | None = Header(default=None, alias="x-goog-api-key"),
) -> Response:
    payload = await request.json()
    print(f"[AgentShield] passthrough matched /v1/{full_path}")

    forward_payload, _, model, session_id, precheck = await _process_for_policy_and_events(
        request, settings.proxy.default_model, payload
    )

    if precheck["blocked"]:
        if "stream" in full_path.lower():
            return _blocked_sse_response(precheck["reason"])
        return _blocked_json_response(precheck["reason"])

    upstream_response = await _forward_to_gemini(f"/v1/{full_path}", forward_payload, x_goog_api_key, request)

    if upstream_response.headers.get("content-type", "").startswith("text/event-stream"):
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "text/event-stream"),
        )

    response_json = _handle_response_recording(session_id, model, upstream_response)
    return JSONResponse(status_code=upstream_response.status_code, content=response_json)
