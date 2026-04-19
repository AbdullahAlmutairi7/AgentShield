#!/usr/bin/env bash
set -e

cd ~/AgentShield
source .venv/bin/activate

echo "[AgentShield] Starting proxy..."
python run_proxy.py
