@echo off
echo Initializing categories for MedEasy scraper...
echo.

REM Try different Python commands
python run_init_categories_local.py
if %errorlevel% equ 0 goto :success

py run_init_categories_local.py
if %errorlevel% equ 0 goto :success

python3 run_init_categories_local.py
if %errorlevel% equ 0 goto :success

echo.
echo Error: Python not found. Please ensure Python is installed and in your PATH.
echo You can also try running the script manually with your Python installation.
echo.
pause
exit /b 1

:success
echo.
echo Category initialization completed successfully!
echo.
pause 