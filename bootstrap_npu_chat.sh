#!/usr/bin/env bash
# Setup and launch helper for the NPU chatbot project.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "npu_chat.py" ]; then
  echo "This script must be run from the project root (where npu_chat.py lives)." >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python 3.12+ is required but neither 'python3' nor 'python' was found." >&2
    exit 1
  fi
fi

PY_VERSION="$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
PY_MAJOR="$($PYTHON_BIN -c 'import sys; print(sys.version_info.major)')"
PY_MINOR="$($PYTHON_BIN -c 'import sys; print(sys.version_info.minor)')"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]; }; then
  echo "Python 3.12 or newer is required (found $PY_VERSION)." >&2
  exit 1
fi

VENV_DIR="${VENV_DIR:-venv}"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in '$VENV_DIR'..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "Using existing virtual environment '$VENV_DIR'."
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
pip install -r requirements.txt

CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  cp config.yaml.template "$CONFIG_FILE"
  echo "Created '$CONFIG_FILE'. Adjust it if you want to change backend settings."
else
  echo "Found existing '$CONFIG_FILE'."
fi

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  cp .env.example "$ENV_FILE"
  echo "Created '$ENV_FILE'. Enter your AnythingLLM API key before running the chat."
else
  echo "Found existing '$ENV_FILE'."
fi

MODEL_NAME="$(python - <<'PY'
import sys, yaml
config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle) or {}
model = (data.get("cpu_fallback") or {}).get("model_path") or ""
print(model)
PY
"$CONFIG_FILE")"

MODEL_PATH=""
if [ -n "$MODEL_NAME" ]; then
  MODEL_PATH="models/${MODEL_NAME}"
fi

NEEDS_MODEL=false
if [ -n "$MODEL_PATH" ]; then
  if [ -f "$MODEL_PATH" ]; then
    echo "Found CPU fallback model at '$MODEL_PATH'."
  else
    NEEDS_MODEL=true
    echo "Missing GGUF model file '$MODEL_PATH'."
  fi
else
  echo "Could not determine the GGUF model name from '$CONFIG_FILE'." >&2
fi

MISSING_API_KEY=false
if grep -q 'your-anythingllm-api-key' "$ENV_FILE"; then
  MISSING_API_KEY=true
fi

if [ "$MISSING_API_KEY" = true ]; then
  cat <<'EON'

Action required:
  - Edit .env and set API_KEY to your AnythingLLM developer token.
    Example: API_KEY="sk-your-secret-key"
EON
fi

if [ "$NEEDS_MODEL" = true ]; then
  cat <<'EOM'

Action required:
  - Download a GGUF model into the models/ directory. Example commands:
      huggingface-cli login
      huggingface-cli download microsoft/Phi-3.5-mini-instruct-gguf Phi-3.5-mini-instruct-Q4_K_M.gguf \
        --local-dir models --local-dir-use-symlinks False
    Adjust cpu_fallback.model_path in config.yaml if you use a different filename.
EOM

  if ! command -v huggingface-cli >/dev/null 2>&1; then
    echo "  - 'huggingface-cli' was not found. Install it via 'pip install huggingface_hub' inside the venv."
  fi
fi

READY=true
if [ "$NEEDS_MODEL" = true ] || [ "$MISSING_API_KEY" = true ]; then
  READY=false
fi

if [ "$READY" = true ]; then
  python preflight_check.py
  python npu_chat.py
else
  echo ""
  echo "Complete the actions above and re-run this script to launch the chatbot."
fi
