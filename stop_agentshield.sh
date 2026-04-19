#!/usr/bin/env bash

echo "[AgentShield] Stopping proxy / telemetry..."
pkill -f run_proxy.py || true
pkill -f run_host_telemetry.py || true
pkill -f uvicorn || true

echo "[AgentShield] Done."
