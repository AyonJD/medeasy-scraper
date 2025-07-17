# PowerShell script to initialize categories using the correct Python path

Write-Host "Initializing categories for MedEasy scraper..." -ForegroundColor Green
Write-Host ""

# Use the actual Python installation path
$pythonPath = "C:\Users\Ayon\AppData\Local\Programs\Python\Python311\python.exe"

# Check if Python exists
if (-not (Test-Path $pythonPath)) {
    Write-Host "Error: Python not found at $pythonPath" -ForegroundColor Red
    Write-Host "Please update the pythonPath in this script." -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "Using Python: $pythonPath" -ForegroundColor Yellow
Write-Host ""

# Run the category initialization
try {
    & $pythonPath run_init_categories_local.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Category initialization completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Error: Category initialization failed." -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "Error running category initialization: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to continue" 