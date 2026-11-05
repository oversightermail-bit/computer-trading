@echo off
REM ============================================================
REM  Restart backend service (Windows)
REM    - Called by admin center "Restart backend" button (PID passed in)
REM    - Manual use: restart-backend.bat [PID]
REM    - Waits 3s so the admin API response can be delivered,
REM      then kills the old process and starts a new instance.
REM ============================================================
setlocal
timeout /t 3 /nobreak >nul
if not "%~1"=="" (
  echo Stopping old backend process PID=%~1 ...
  taskkill /F /PID %~1 >nul 2>nul
  timeout /t 2 /nobreak >nul
)
call "%~dp0start-backend.bat" --no-pause
endlocal
