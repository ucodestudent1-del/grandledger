@echo off
setlocal

echo Setting up GrandLedger development environment...

REM Copy env if not exists
if not exist .env (
    copy .env.example .env
    echo Created .env from .env.example
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Install frontend dependencies
echo Installing frontend dependencies...
cd web
npm install
cd ..

REM Run database migrations
echo Running database migrations...
alembic upgrade head

echo Setup complete!
echo.
echo To start the dev servers:
echo   API:    uvicorn src.main:app --reload --port 8000
echo   Web:    cd web && npm run dev
