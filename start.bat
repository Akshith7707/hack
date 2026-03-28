@echo off
echo ========================================
echo   FlexCode - Starting Application
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "FlexCode Backend" cmd /k "cd backend && echo Starting backend on http://localhost:8000 && uvicorn main:app --reload --port 8000"

timeout /t 3 >nul

echo [2/2] Starting Frontend Server...
start "FlexCode Frontend" cmd /k "cd frontend && echo Starting frontend on http://localhost:5173 && npm run dev"

echo.
echo ========================================
echo   FlexCode is starting up!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open frontend in browser...
pause >nul

start http://localhost:5173

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
