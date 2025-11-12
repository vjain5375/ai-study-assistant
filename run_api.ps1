# FastAPI Backend Server Startup Script
Write-Host "🚀 Starting FastAPI Backend Server..." -ForegroundColor Green
Write-Host ""

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
try {
    python -c "import fastapi, uvicorn" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✅ Dependencies OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Missing dependencies. Installing..." -ForegroundColor Red
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "📍 API will be at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "📚 API docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "💚 Health check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "⏳ Please wait 5-10 seconds for the server to start..." -ForegroundColor Yellow
Write-Host ""

# Start the API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

