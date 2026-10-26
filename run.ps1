Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  TECHNICAL DOCUMENT TERMINOLOGY & CONCEPT RELATIONSHIP MAPPER" -ForegroundColor Yellow
Write-Host "  Starting Unified Flask & React Flow Application Server" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

$env:PYTHONPATH = "."
python run.py
