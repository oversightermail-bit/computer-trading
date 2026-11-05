#!/usr/bin/env bash
# ============================================================
# Restart backend service (Linux server)
#   - Called by admin center "Restart backend" button (PID passed in)
#   - Manual use: ./restart-backend.sh [PID]
#   - Waits 3s so the admin API response can be delivered,
#     then kills the old process and starts a new instance.
# ============================================================
ROOT="$(cd "$(dirname "$0")" && pwd)"
sleep 3
OLD_PID="${1:-$(cat "$ROOT/后端/target/app.pid" 2>/dev/null || true)}"
if [ -n "$OLD_PID" ]; then
  echo "Stopping old backend process PID=$OLD_PID ..."
  kill "$OLD_PID" 2>/dev/null || true
  sleep 2
fi
exec "$ROOT/start-backend.sh"
