# PowerShell script to initialize categories using SQL

Write-Host "Initializing categories using SQL script..." -ForegroundColor Green
Write-Host ""

# Check if SQLite is available
try {
    $sqliteVersion = & sqlite3 --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found SQLite: $sqliteVersion" -ForegroundColor Yellow
    } else {
        throw "SQLite not found"
    }
} catch {
    Write-Host "Error: SQLite not found. Please install SQLite from https://www.sqlite.org/download.html" -ForegroundColor Red
    Write-Host "Or add SQLite to your PATH if already installed." -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if database exists, create if not
if (-not (Test-Path "medeasy_local.db")) {
    Write-Host "Creating new SQLite database..." -ForegroundColor Yellow
    echo ".databases" | sqlite3 medeasy_local.db
}

# Run the SQL script
Write-Host "Running category initialization SQL script..." -ForegroundColor Yellow
$sqlScript = Get-Content "scripts/init_categories.sql" -Raw
$sqlScript | sqlite3 medeasy_local.db

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Category initialization completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Categories created:" -ForegroundColor Cyan
    sqlite3 medeasy_local.db "SELECT id, name, slug FROM categories ORDER BY id;"
} else {
    Write-Host ""
    Write-Host "Error: Failed to run SQL script." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to continue" 