#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_LOG_LEVEL="${BATHYMESH_LOG_LEVEL:-DEBUG}"

if command -v stdbuf >/dev/null 2>&1; then
  LINE_BUFFER=(stdbuf -oL -eL)
else
  LINE_BUFFER=()
fi

cleanup() {
  trap - INT TERM EXIT

  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    # Wait briefly for graceful shutdown
    sleep 0.5
    # Force kill if still alive
    kill -9 "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    # Wait briefly for graceful shutdown
    sleep 0.5
    # Force kill if still alive
    kill -9 "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
}

cleanup_stale_ports() {
  # Kill any existing processes bound to port 3000 (frontend) and 8000 (backend)
  for port in 3000 8000; do
    if command -v lsof >/dev/null 2>&1; then
      # Using lsof to find and kill processes on specific ports
      pids=$(lsof -ti :$port 2>/dev/null || true)
      if [[ -n "$pids" ]]; then
        echo "[runner] Cleaning up stale process on port $port: $pids"
        kill -9 $pids 2>/dev/null || true
        sleep 0.2
      fi
    elif command -v ss >/dev/null 2>&1; then
      # Fallback for systems without lsof
      pid=$(ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $NF}' | cut -d'/' -f1)
      if [[ -n "$pid" && "$pid" != "-" ]]; then
        echo "[runner] Cleaning up stale process on port $port: $pid"
        kill -9 "$pid" 2>/dev/null || true
        sleep 0.2
      fi
    fi
  done
}

trap cleanup INT TERM EXIT

cleanup_stale_ports

(
  cd "$BACKEND_DIR"
  "${LINE_BUFFER[@]}" env BATHYMESH_LOG_LEVEL="$BACKEND_LOG_LEVEL" uv run serve 2>&1 | sed -u 's/^/[backend] /'
) &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  "${LINE_BUFFER[@]}" bun run dev 2>&1 | sed -u 's/^/[frontend] /'
) &
FRONTEND_PID=$!

set +e
wait -n "$BACKEND_PID" "$FRONTEND_PID"
EXIT_STATUS=$?
set -e

if [[ $EXIT_STATUS -ne 0 ]]; then
  echo "[runner] One server exited with status $EXIT_STATUS; shutting down both."
else
  echo "[runner] One server exited cleanly; shutting down both."
fi

cleanup
exit "$EXIT_STATUS"
