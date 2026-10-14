@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    python -m venv ".venv"
    if errorlevel 1 exit /b 1
    call ".venv\Scripts\activate.bat"
)
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
start "" "http://127.0.0.1:8000"
python -m uvicorn dashboard.server:app --host 127.0.0.1 --port 8000
