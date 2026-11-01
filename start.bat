@echo off
cd /d "%~dp0"
echo.
echo  StellaScrapes - starting...
echo.

where node >nul 2>&1
if %errorlevel% neq 0 (
  echo  ERROR: Node.js not found. Install from https://nodejs.org
  pause
  exit /b 1
)

if not exist node_modules (
  echo  Installing dependencies...
  call npm install
  echo.
)

start http://localhost:3100
node server.js
pause
