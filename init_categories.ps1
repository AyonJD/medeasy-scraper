# PowerShell script to initialize categories for MedEasy scraper

Write-Host "Initializing categories for MedEasy scraper..." -ForegroundColor Green
Write-Host ""

# Try to find Python
$pythonCommands = @("python", "py", "python3")

foreach ($cmd in $pythonCommands) {
    try {
        $result = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Found Python: $cmd" -ForegroundColor Yellow
            Write-Host "Running category initialization..." -ForegroundColor Yellow
            
            & $cmd run_init_categories_local.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "Category initialization completed successfully!" -ForegroundColor Green
                Write-Host ""
                Read-Host "Press Enter to continue"
                exit 0
            } else {
                Write-Host "Error running category initialization with $cmd" -ForegroundColor Red
            }
        }
    } catch {
        # Command not found, try next one
        continue
    }
}

Write-Host ""
Write-Host "Error: Python not found. Please ensure Python is installed and in your PATH." -ForegroundColor Red
Write-Host "You can also try running the script manually with your Python installation." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"
exit 1 