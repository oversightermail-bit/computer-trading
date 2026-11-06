#!/usr/bin/env bash
# ============================================================
# Start backend service (Linux server)
#   chmod +x start-backend.sh && ./start-backend.sh
#   Requires JDK 17+: set JAVA_HOME or put java in PATH
#   Auto-locates the backend jar (newest match wins), in order:
#     1. BACKEND_JAR environment variable
#     2. <root>/target/hw-price-backend-*.jar
#     3. <root>/*/target/hw-price-backend-*.jar
#     4. <root>/*/*/target/hw-price-backend-*.jar
#     5. any <root>/*/target/*.jar (excluding sources/javadoc/original)
#   Auto-locates Java: JAVA_HOME -> common JDK dirs -> PATH
#   Site: http://127.0.0.1:8080   Log: <jar dir>/app.log
# ============================================================
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"

# ---------- 0. 本地密钥（不入 Git）：设置 DB_PASSWORD / JWT_SECRET ----------
if [ -f "$ROOT/backend-env.sh" ]; then . "$ROOT/backend-env.sh"; fi

# ---------- 1. Locate the backend jar ----------
JAR="${BACKEND_JAR:-}"
if [ -n "$JAR" ] && [ ! -f "$JAR" ]; then JAR=""; fi
if [ -z "$JAR" ]; then JAR="$(ls -t "$ROOT"/target/hw-price-backend-*.jar 2>/dev/null | head -n1)"; fi
if [ -z "$JAR" ]; then JAR="$(ls -t "$ROOT"/*/target/hw-price-backend-*.jar 2>/dev/null | head -n1)"; fi
if [ -z "$JAR" ]; then JAR="$(ls -t "$ROOT"/*/*/target/hw-price-backend-*.jar 2>/dev/null | head -n1)"; fi
if [ -z "$JAR" ]; then JAR="$(ls -t "$ROOT"/*/target/*.jar 2>/dev/null | grep -vE '(sources|javadoc|original)\.jar$' | head -n1)"; fi

if [ -z "$JAR" ]; then
  echo "[ERROR] Backend jar not found under $ROOT"
  echo "Build it first: cd <backend-dir> && mvn -DskipTests package"
  echo "Or set BACKEND_JAR to the full path of the jar."
  exit 1
fi

APP_DIR="$(dirname "$JAR")"
LOG="$APP_DIR/app.log"
PID_FILE="$APP_DIR/app.pid"
echo "Found backend jar: $JAR"

# ---------- 2. Already running? ----------
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
  echo "[INFO] Backend already running (PID $(cat "$PID_FILE"))"
  exit 0
fi
rm -f "$PID_FILE"

# ---------- 3. Locate Java (JDK 17+) ----------
JAVA_BIN=""
if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
  JAVA_BIN="$JAVA_HOME/bin/java"
fi
if [ -z "$JAVA_BIN" ]; then
  JAVA_BIN="$(ls /usr/lib/jvm/*/bin/java /opt/*jdk*/bin/java /opt/jdk*/bin/java /usr/local/*jdk*/bin/java 2>/dev/null | sort -V | tail -n1)"
fi
if [ -z "$JAVA_BIN" ] && command -v java >/dev/null 2>&1; then
  JAVA_BIN="$(command -v java)"
fi
if [ -z "$JAVA_BIN" ]; then
  echo "[ERROR] java (JDK 17+) not found. Install it or set JAVA_HOME."
  exit 1
fi

# ---------- 4. Verify Java version (JDK 17+) ----------
JAVA_VER="$("$JAVA_BIN" -version 2>&1 | head -n1)"
MAJOR="$(printf '%s\n' "$JAVA_VER" | sed -nE 's/.*version "([0-9]+).*/\1/p')"
if [ -n "$MAJOR" ] && [ "$MAJOR" -lt 17 ]; then
  echo "[ERROR] $JAVA_VER is too old; JDK 17+ is required."
  exit 1
fi

echo "Starting backend service with: $JAVA_BIN"
echo "Java: $JAVA_VER"
echo "Jar:  $JAR"
echo "Site: http://127.0.0.1:8080   Log: $LOG"
nohup "$JAVA_BIN" -jar "$JAR" >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "Started, PID $(cat "$PID_FILE")"
