@echo off
echo Initializing categories using SQL script...
echo.

REM Check if SQLite database exists
if not exist "medeasy_local.db" (
    echo Creating new SQLite database...
    echo .databases > temp.sql
    sqlite3 medeasy_local.db < temp.sql
    del temp.sql
)

REM Run the SQL script
echo Running category initialization SQL script...
sqlite3 medeasy_local.db < scripts/init_categories.sql

if %errorlevel% equ 0 (
    echo.
    echo Category initialization completed successfully!
    echo.
    echo Categories created:
    sqlite3 medeasy_local.db "SELECT id, name, slug FROM categories ORDER BY id;"
) else (
    echo.
    echo Error: Failed to run SQL script. Make sure SQLite is installed.
    echo You can install SQLite from: https://www.sqlite.org/download.html
)

echo.
pause 