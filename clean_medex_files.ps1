# MedEx Data Cleanup Script (PowerShell)
# Remove all HTML and image files from scraped data

Write-Host "🧹 MedEx Data File Cleanup" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Count existing files
$htmlPath = "static\html\2025\07"
$imagePath = "static\images\2025\07"

$htmlCount = 0
$imageCount = 0

if (Test-Path $htmlPath) {
    $htmlCount = (Get-ChildItem $htmlPath -File -Recurse).Count
}

if (Test-Path $imagePath) {
    $imageCount = (Get-ChildItem $imagePath -File -Recurse).Count
}

Write-Host "📂 Found files to clean:" -ForegroundColor Yellow
Write-Host "   • HTML files: $htmlCount" -ForegroundColor White
Write-Host "   • Image files: $imageCount" -ForegroundColor White
Write-Host ""

if ($htmlCount -eq 0 -and $imageCount -eq 0) {
    Write-Host "✅ No files to clean - already clean!" -ForegroundColor Green
    exit 0
}

# Ask for confirmation
$confirmation = Read-Host "❓ Are you sure you want to delete all files? (yes/no)"
if ($confirmation -notmatch "^(yes|y)$") {
    Write-Host "❌ Cleanup cancelled by user" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting cleanup..." -ForegroundColor Green
Write-Host "-" * 30 -ForegroundColor Gray

# Clean HTML files
if ($htmlCount -gt 0) {
    Write-Host "🗑️  Deleting $htmlCount HTML files..." -ForegroundColor Yellow
    try {
        Remove-Item "$htmlPath\*" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ HTML files deleted successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error deleting HTML files: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Clean image files  
if ($imageCount -gt 0) {
    Write-Host "🖼️  Deleting $imageCount image files..." -ForegroundColor Yellow
    try {
        Remove-Item "$imagePath\*" -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Image files deleted successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error deleting image files: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Clean log files
$logFiles = @("logs\medex_scraper.log", "medex_scraper.log")
$logCount = 0

foreach ($logFile in $logFiles) {
    if (Test-Path $logFile) {
        try {
            Remove-Item $logFile -Force
            Write-Host "🗑️  Deleted log file: $logFile" -ForegroundColor Yellow
            $logCount++
        }
        catch {
            Write-Host "⚠️  Failed to delete $logFile" -ForegroundColor Orange
        }
    }
}

if ($logCount -gt 0) {
    Write-Host "✅ Deleted $logCount log files" -ForegroundColor Green
}

# Remove empty directories
try {
    if (Test-Path "static\html\2025\07" -and (Get-ChildItem "static\html\2025\07" -Force | Measure-Object).Count -eq 0) {
        Remove-Item "static\html\2025\07" -Force
        Write-Host "📂 Removed empty HTML directory" -ForegroundColor Gray
    }
    
    if (Test-Path "static\images\2025\07" -and (Get-ChildItem "static\images\2025\07" -Force | Measure-Object).Count -eq 0) {
        Remove-Item "static\images\2025\07" -Force  
        Write-Host "📂 Removed empty images directory" -ForegroundColor Gray
    }
}
catch {
    # Ignore errors for directory cleanup
}

Write-Host ""
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "🎉 File cleanup completed!" -ForegroundColor Green
Write-Host "   Note: Database records were NOT touched." -ForegroundColor Yellow
Write-Host "   Use clean_medex_data.py for full cleanup including database." -ForegroundColor Yellow
Write-Host "" 