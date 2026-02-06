@echo off
cls
echo ===================================================
echo    FACE ATTENDANCE SYSTEM - PREMIUM HUB
echo ===================================================
echo.
echo [1] Launch Desktop GUI (Scanner + Enrollment)
echo [2] Start Admin API server (FastAPI)
echo [3] Run Web Dashboard (Streamlit)
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Starting GUI...
    .\env\Scripts\python.exe gui/app.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Starting API server...
    .\env\Scripts\python.exe -m uvicorn api.main:app --reload
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Starting Web Dashboard...
    .\env\Scripts\python.exe -m streamlit run dashboard/dashboard.py
    goto end
)

if "%choice%"=="4" exit

:end
echo.
echo Press any key to return to menu...
pause >nul
goto start
