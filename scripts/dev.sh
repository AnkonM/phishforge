#!/usr/bin/env bash
# Starts the backend (uvicorn, reload) and frontend (vite) dev servers
# together, and tears both down on Ctrl-C / exit.
set -euo pipefail
cd "$(dirname "$0")/.."

PHISHFORGE_DEMO="${PHISHFORGE_DEMO:-}"

cleanup() {
  echo ""
  echo "Stopping dev servers..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

source .venv/bin/activate
echo "Starting backend on http://127.0.0.1:8000 (mode: ${PHISHFORGE_DEMO:+demo}${PHISHFORGE_DEMO:-auto})"
PHISHFORGE_DEMO="$PHISHFORGE_DEMO" python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:5173"
(cd web && npm run dev) &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
