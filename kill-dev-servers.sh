#!/usr/bin/env bash
set -euo pipefail

PORTS=(3000 8000)

killed_any=0

kill_pid() {
  local pid="$1"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "[kill] Terminating PID $pid"
    kill "$pid" 2>/dev/null || true
    sleep 0.3
    if kill -0 "$pid" 2>/dev/null; then
      echo "[kill] Force killing PID $pid"
      kill -9 "$pid" 2>/dev/null || true
    fi
    killed_any=1
  fi
}

kill_from_port() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill_pid "$pid"
    done < <(lsof -ti :"$port" 2>/dev/null | sort -u)
    return
  fi

  if command -v fuser >/dev/null 2>&1; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill_pid "$pid"
    done < <(fuser "$port"/tcp 2>/dev/null | tr ' ' '\n' | sed '/^$/d' | sort -u)
    return
  fi

  if command -v ss >/dev/null 2>&1; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill_pid "$pid"
    done < <(
      ss -tlnp 2>/dev/null \
        | awk -v p=":$port" '$4 ~ p {print $NF}' \
        | sed -E 's/.*pid=([0-9]+).*/\1/' \
        | sed '/^$/d' \
        | sort -u
    )
    return
  fi

  echo "[kill] Skipping port $port: no supported tool found (lsof, fuser, or ss)."
}

for port in "${PORTS[@]}"; do
  kill_from_port "$port"
done

# Fallback in case processes survived but released ports already.
if command -v pkill >/dev/null 2>&1; then
  pkill -f "uv run serve" 2>/dev/null || true
  pkill -f "bun --hot src/index.ts" 2>/dev/null || true
fi

if [[ "$killed_any" -eq 1 ]]; then
  echo "[kill] Dev server cleanup complete."
else
  echo "[kill] No matching dev server processes found."
fi
