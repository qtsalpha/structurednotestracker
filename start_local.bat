@echo off
REM Quick Start Script for Windows
REM Structured Notes Tracker

echo 🚀 Starting Structured Notes Tracker...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    if exist ".env.example" (
        echo 📝 Creating .env file from .env.example...
        copy .env.example .env
        echo ⚠️  Please edit .env file with your settings if needed
    )
)

echo.
echo ✨ All set! Starting Streamlit app...
echo 📱 The app will open in your browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run Streamlit
streamlit run app_new.py


