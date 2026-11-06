@echo off
REM ============================================================
REM  Restart backend service (Windows)
REM    - Called by admin center "Restart backend" button (PID passed in)
REM    - Manual use: restart-backend.bat [PID]
REM    - Waits 3s so the admin API response can be delivered,
REM      then kills the old process and starts a new instance.
REM ============================================================
setlocal
REM ping-based waits: work with or without console stdin
REM (timeout fails with "Input redirection is not supported"
REM  when the admin center launches this script detached)
ping -n 4 127.0.0.1 >nul
if not "%~1"=="" (
  echo Stopping old backend process PID=%~1 ...
  taskkill /F /PID %~1 >nul 2>nul
  ping -n 3 127.0.0.1 >nul
)
call "%~dp0start-backend.bat" --no-pause
endlocal
