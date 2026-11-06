@echo off
REM ============================================================
REM  Start backend service (Windows)
REM    - Double-click to run, or run in command line
REM    - Pass --no-pause to skip the final pause (restart script uses it)
REM    - Server deployment: install JDK 17+ and run this script
REM    - Auto-locates the backend jar, in priority order:
REM        1. Optional 1st argument: start-backend.bat D:\path\app.jar
REM        2. BACKEND_JAR environment variable
REM        3. <root>\target\hw-price-backend-*.jar
REM        4. <root>\<dir>\target\hw-price-backend-*.jar
REM        5. <root>\<dir>\<dir>\target\hw-price-backend-*.jar
REM        6. any <root>\<dir>\target\*.jar (excluding sources/javadoc)
REM    - Auto-locates Java: JAVA_HOME -> JetBrains JBR -> Program Files\Java -> PATH
REM    - Site: http://127.0.0.1:8080
REM ============================================================
setlocal
set "ROOT=%~dp0"

REM ---------- 0. 本地密钥（不入 Git）：设置 DB_PASSWORD / JWT_SECRET ----------
if exist "%~dp0backend-env.bat" call "%~dp0backend-env.bat"

REM ---------- 1. Locate the backend jar ----------
set "JAR="
if not "%~1"=="" if /i not "%~1"=="--no-pause" if exist "%~1" set "JAR=%~f1"
if not defined JAR if defined BACKEND_JAR if exist "%BACKEND_JAR%" set "JAR=%BACKEND_JAR%"
if not defined JAR for %%F in ("%ROOT%target\hw-price-backend-*.jar") do if exist "%%F" set "JAR=%%~fF"
if not defined JAR for /d %%D in ("%ROOT%*") do if not defined JAR for %%F in ("%%D\target\hw-price-backend-*.jar") do if exist "%%F" set "JAR=%%~fF"
if not defined JAR for /d %%D in ("%ROOT%*") do for /d %%E in ("%%D\*") do if not defined JAR for %%F in ("%%E\target\hw-price-backend-*.jar") do if exist "%%F" set "JAR=%%~fF"
if not defined JAR for /d %%D in ("%ROOT%*") do if not defined JAR for %%F in ("%%D\target\*.jar") do if exist "%%F" if not defined JAR (
    echo %%~nxF | findstr /i "sources javadoc original" >nul || set "JAR=%%~fF"
)

if not defined JAR (
    echo [ERROR] Backend jar not found under: %ROOT%
    echo   Build it first: run "mvn -DskipTests package" in the backend project directory,
    echo   or pass the jar path: start-backend.bat D:\path\app.jar
    echo   or set the BACKEND_JAR environment variable.
    goto :done
)
echo Found backend jar: %JAR%
set "LOG=%~dp0backend-runtime.log"

REM ---------- 2. Already listening on port 8080? ----------
netstat -ano | findstr ":8080 " | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
    echo [INFO] Port 8080 already listening, backend may already be running.
    goto :done
)

REM ---------- 3. Locate Java (JDK 17+) ----------
set "JAVA_BIN="
if defined JAVA_HOME if exist "%JAVA_HOME%\bin\java.exe" set "JAVA_BIN=%JAVA_HOME%\bin\java.exe"
if not defined JAVA_BIN for /d %%I in ("%ProgramFiles%\JetBrains\IntelliJ IDEA*") do if exist "%%I\jbr\bin\java.exe" if not defined JAVA_BIN set "JAVA_BIN=%%I\jbr\bin\java.exe"
if not defined JAVA_BIN for /d %%I in ("%ProgramFiles%\Java\*") do if exist "%%I\bin\java.exe" if not defined JAVA_BIN set "JAVA_BIN=%%I\bin\java.exe"
if not defined JAVA_BIN for /d %%I in ("%ProgramFiles(x86)%\Java\*") do if exist "%%I\bin\java.exe" if not defined JAVA_BIN set "JAVA_BIN=%%I\bin\java.exe"
if not defined JAVA_BIN where java >nul 2>nul && set "JAVA_BIN=java"
if not defined JAVA_BIN (
    echo [ERROR] Java runtime ^(JDK/JRE 17+^) not found. Install it or set JAVA_HOME.
    goto :done
)

REM ---------- 4. Verify Java version (JDK 17+) ----------
set "VER_STR="
set "VER_TMP=%~dp0.javaver-check.tmp"
del "%VER_TMP%" >nul 2>nul
"%JAVA_BIN%" -version 2>&1 | findstr /i "version" > "%VER_TMP%" 2>nul
if exist "%VER_TMP%" for /f "usebackq tokens=3" %%V in ("%VER_TMP%") do set "VER_STR=%%V"
del "%VER_TMP%" >nul 2>nul
if defined VER_STR set "VER_STR=%VER_STR:"=%"
set "MAJOR="
if defined VER_STR for /f "delims=." %%M in ("%VER_STR%") do set "MAJOR=%%M"
if not defined MAJOR goto :version_ok
echo %MAJOR% | findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 goto :version_ok
if %MAJOR% LSS 17 (
    echo [ERROR] Java %VER_STR% is too old; JDK 17+ is required.
    goto :done
)
:version_ok

echo Starting backend service with: %JAVA_BIN%
if defined VER_STR echo Java version: %VER_STR%
echo Jar:  %JAR%
echo Site: http://127.0.0.1:8080
echo Log:  %LOG%
"%JAVA_BIN%" -jar "%JAR%" >> "%LOG%" 2>&1

:done
if /i not "%~1"=="--no-pause" pause
endlocal
