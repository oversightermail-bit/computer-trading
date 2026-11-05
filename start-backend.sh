#!/usr/bin/env bash
# ============================================================
# Start backend service (Linux server)
#   chmod +x start-backend.sh && ./start-backend.sh
#   Requires JDK 17+: set JAVA_HOME or put java in PATH
#   Site: http://127.0.0.1:8080   Log: <root>/后端/target/app.log
# ============================================================
ROOT="$(cd "$(dirname "$0")" && pwd)"
JAR="$ROOT/后端/target/hw-price-backend-1.0.0.jar"
LOG="$ROOT/后端/target/app.log"
PID_FILE="$ROOT/后端/target/app.pid"

if [ ! -f "$JAR" ]; then
  echo "[ERROR] Backend jar not found: $JAR"
  echo "Build it first: cd 后端 && mvn -DskipTests package"
  exit 1
fi

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
  echo "[INFO] Backend already running (PID $(cat "$PID_FILE"))"
  exit 0
fi

if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]; then
  JAVA_BIN="$JAVA_HOME/bin/java"
else
  JAVA_BIN="$(command -v java || true)"
fi
if [ -z "$JAVA_BIN" ]; then
  echo "[ERROR] java (JDK 17+) not found. Install it or set JAVA_HOME."
  exit 1
fi

echo "Starting backend service with: $JAVA_BIN"
echo "Site: http://127.0.0.1:8080   Log: $LOG"
nohup "$JAVA_BIN" -jar "$JAR" >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "Started, PID $(cat "$PID_FILE")"
