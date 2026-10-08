@echo off
wsl -d Ubuntu-22.04 -u root --cd "%~dp0." -- docker compose up --no-build -d
if errorlevel 1 (
  pause
  exit /b 1
)
start "" "http://localhost:8080/vnc.html?autoconnect=1&resize=scale"
wsl -d Ubuntu-22.04 -u root --cd "%~dp0." -- docker compose up --no-build
