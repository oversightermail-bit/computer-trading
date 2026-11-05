@echo off
REM ============================================================
REM  Start backend service (Windows)
REM    - Double-click to run, or run in command line
REM    - Pass --no-pause to skip the final pause (restart script uses it)
REM    - Server deployment: install JDK 17+ and run this script
REM    - Site: http://127.0.0.1:8080
REM ============================================================
setlocal
set "ROOT=%~dp0"

REM Locate the backend jar by scanning project subdirectories
set "JAR="
for /d %%D in ("%ROOT%*") do if exist "%%D\target\hw-price-backend-1.0.0.jar" set "JAR=%%D\target\hw-price-backend-1.0.0.jar"
if not defined JAR (
  echo [ERROR] Backend jar not found under %ROOT%
  echo Build it first: run "mvn -DskipTests package" in the backend project directory.
  goto :done
)
set "LOG=%~dp0backend-runtime.log"

netstat -ano | findstr ":8080 " | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo [INFO] Port 8080 already listening, backend may already be running.
  goto :done
)

set "JAVA_BIN="
if exist "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\jbr\bin\java.exe" set "JAVA_BIN=C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\jbr\bin\java.exe"
if not defined JAVA_BIN if defined JAVA_HOME set "JAVA_BIN=%JAVA_HOME%\bin\java.exe"
if not defined JAVA_BIN where java >nul 2>nul && set "JAVA_BIN=java"
if not defined JAVA_BIN (
  echo [ERROR] Java runtime ^(JDK/JRE 17+^) not found. Install it or set JAVA_HOME.
  goto :done
)

echo Starting backend service with: %JAVA_BIN%
echo Jar:  %JAR%
echo Site: http://127.0.0.1:8080
echo Log:  %LOG%
"%JAVA_BIN%" -jar "%JAR%" >> "%LOG%" 2>&1

:done
if /i not "%~1"=="--no-pause" pause
endlocal
