#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if command -v stdbuf >/dev/null 2>&1; then
  LINE_BUFFER=(stdbuf -oL -eL)
else
  LINE_BUFFER=()
fi

cleanup() {
  trap - INT TERM EXIT

  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

(
  cd "$BACKEND_DIR"
  "${LINE_BUFFER[@]}" uv run serve 2>&1 | sed -u 's/^/[backend] /'
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
