#!/usr/bin/env bash
set -e

cd ~/AgentShield
source .venv/bin/activate

echo "[AgentShield] Starting host telemetry..."
python run_host_telemetry.py
