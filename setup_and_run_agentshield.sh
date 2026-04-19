#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/AgentShield"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
ENV_FILE="$PROJECT_DIR/.agentshield_env"
PROXY_LOG="$PROJECT_DIR/proxy.log"
TELEMETRY_LOG="$PROJECT_DIR/telemetry.log"

echo "=== AgentShield Setup + Run ==="

if [ ! -d "$PROJECT_DIR" ]; then
  echo "ERROR: $PROJECT_DIR does not exist."
  exit 1
fi

if [ ! -f "$OPENCLAW_CONFIG" ]; then
  echo "ERROR: OpenClaw config not found at $OPENCLAW_CONFIG"
  exit 1
fi

read -rsp "Enter GEMINI API KEY: " GEMINI_KEY
echo
if [ -z "${GEMINI_KEY:-}" ]; then
  echo "ERROR: Gemini API key cannot be empty."
  exit 1
fi

read -rp "Enter AgentShield policy judge model [gemini-2.5-flash-lite]: " POLICY_MODEL
POLICY_MODEL="${POLICY_MODEL:-gemini-2.5-flash-lite}"

echo "Stopping old AgentShield processes if any..."
pkill -f run_proxy.py || true
pkill -f run_host_telemetry.py || true
pkill -f uvicorn || true

echo "Updating OpenClaw config..."
python3 - <<PY
import json
from pathlib import Path

config_path = Path("$OPENCLAW_CONFIG")
data = json.loads(config_path.read_text())

data.setdefault("models", {})
data["models"].setdefault("providers", {})
data["models"]["providers"]["google"] = {
    "apiKey": "$GEMINI_KEY",
    "baseUrl": "http://127.0.0.1:8787",
    "models": []
}

data.setdefault("agents", {})
data["agents"].setdefault("defaults", {})
data["agents"]["defaults"].setdefault("model", {})
data["agents"]["defaults"]["model"]["primary"] = "google/gemini-2.5-flash-lite"

data["agents"]["defaults"].setdefault("models", {})
data["agents"]["defaults"]["models"]["google/gemini-2.5-flash-lite"] = {}
data["agents"]["defaults"]["models"]["google/gemini-3.1-pro-preview"] = {}
data["agents"]["defaults"]["models"]["google/gemini-3.1-flash-lite-preview"] = {}

config_path.write_text(json.dumps(data, indent=2))
print(f"Updated {config_path}")
PY

echo "Writing AgentShield environment file..."
cat > "$ENV_FILE" <<EOF
export GEMINI_API_KEY='$GEMINI_KEY'
export GEMINI_POLICY_API_KEY='$GEMINI_KEY'
export GEMINI_POLICY_MODEL='$POLICY_MODEL'
export GEMINI_POLICY_BASE_URL='https://generativelanguage.googleapis.com'
export AGENTSHIELD_LLM_JUDGE_ENABLED='true'
export AGENTSHIELD_LLM_JUDGE_THRESHOLD='0.78'
export AGENTSHIELD_LLM_JUDGE_FAIL_CLOSED='false'
EOF

echo "Recreating virtual environment..."
cd "$PROJECT_DIR"
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies..."
python -m pip install fastapi uvicorn httpx python-dotenv sqlalchemy psutil watchdog pyyaml

echo "Bootstrapping database..."
source "$ENV_FILE"
python bootstrap.py || true

echo "Making launcher scripts executable..."
chmod +x start_proxy.sh start_telemetry.sh stop_agentshield.sh || true

echo "Starting AgentShield proxy..."
nohup bash -lc "cd '$PROJECT_DIR' && source .venv/bin/activate && source '$ENV_FILE' && python run_proxy.py" > "$PROXY_LOG" 2>&1 &

sleep 3

echo "Starting AgentShield telemetry..."
nohup bash -lc "cd '$PROJECT_DIR' && source .venv/bin/activate && source '$ENV_FILE' && python run_host_telemetry.py" > "$TELEMETRY_LOG" 2>&1 &

sleep 3

echo
echo "=== Done ==="
echo "OpenClaw config updated: $OPENCLAW_CONFIG"
echo "Environment saved to:    $ENV_FILE"
echo "Proxy log:               $PROXY_LOG"
echo "Telemetry log:           $TELEMETRY_LOG"
echo
echo "Dashboard: http://127.0.0.1:8787/"
echo
echo "Next important step:"
echo "1) Restart OpenClaw manually so it reloads the updated config."
echo "2) Send a safe prompt first."
echo "3) Then send a malicious prompt."
echo
echo "Useful checks:"
echo "tail -f $PROXY_LOG"
echo "tail -f $TELEMETRY_LOG"
echo "curl http://127.0.0.1:8787/health"
