@echo off
REM Quick start script for BOOM Wizard Engine (Windows)

echo Starting BOOM Wizard Engine...

REM Check if .env exists
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo WARNING: Please edit .env with your API keys before continuing!
    echo Required: OPENAI_API_KEY or other LLM provider key
    exit /b 1
)

REM Check if Docker is available
docker-compose --version >nul 2>&1
if %errorlevel% == 0 (
    echo Starting with Docker Compose...
    docker-compose up -d
    echo Services started!
    echo   - API: http://localhost:8000
    echo   - Docs: http://localhost:8000/docs
    echo   - Redis: localhost:6379
    echo.
    echo View logs: docker-compose logs -f wizard_engine
    echo Stop: docker-compose down
) else (
    echo Starting with Python...
    
    REM Check if venv exists
    if not exist venv (
        echo Creating virtual environment...
        python -m venv venv
    )
    
    REM Activate venv
    call venv\Scripts\activate.bat
    
    REM Install dependencies
    echo Installing dependencies...
    pip install -r requirements.txt
    
    REM Start the application
    echo Starting API server...
    python -m app.main
)
