@echo off
REM Streamlit UI Launcher for Brief2Bill
REM This script activates the virtual environment and runs the Streamlit app

echo ========================================
echo   Brief2Bill - Streamlit UI Launcher
echo ========================================
echo.

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install streamlit if not already installed
echo [2/3] Checking dependencies...
pip install streamlit --quiet

REM Run Streamlit app
echo [3/3] Starting Streamlit UI...
echo.
echo ========================================
echo   Opening in browser...
echo   URL: http://localhost:8501
echo ========================================
echo.
streamlit run streamlit_app.py

pause

