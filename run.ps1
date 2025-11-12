# PowerShell launcher for AI Study Assistant
# Usage: .\run.ps1 [host] [port]
# Example: .\run.ps1 localhost 8080

param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8501
)

Write-Host "Starting AI Study Assistant..." -ForegroundColor Green
Write-Host "Host: $Host" -ForegroundColor Cyan
Write-Host "Port: $Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the app at: http://${Host}:${Port}" -ForegroundColor Yellow
Write-Host ""

python main.py --host $Host --port $Port

