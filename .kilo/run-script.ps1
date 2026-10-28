@echo off
setlocal

echo Starting GrandLedger dev servers...

start "API" cmd /c "uvicorn src.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

cd web
start "Web" cmd /c "npm run dev"
cd ..

echo API:   http://localhost:8000
echo Web:   http://localhost:3000
echo Docs:  http://localhost:8000/docs
