@echo off
echo Initializing categories for MedEasy scraper...
echo.

REM Use the actual Python installation path
set PYTHON_PATH=C:\Users\Ayon\AppData\Local\Programs\Python\Python311\python.exe

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo Error: Python not found at %PYTHON_PATH%
    echo Please update the PYTHON_PATH in this batch file.
    pause
    exit /b 1
)

echo Using Python: %PYTHON_PATH%
echo.

REM Run the category initialization
"%PYTHON_PATH%" run_init_categories_local.py

if %errorlevel% equ 0 (
    echo.
    echo Category initialization completed successfully!
) else (
    echo.
    echo Error: Category initialization failed.
)

echo.
pause 