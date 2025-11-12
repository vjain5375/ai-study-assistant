# Start AI Study Assistant
Write-Host "🚀 Starting AI Study Assistant..." -ForegroundColor Green
Write-Host ""

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
try {
    python -c "import streamlit; import fitz; print('✅ All dependencies OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "❌ Missing dependencies. Installing..." -ForegroundColor Red
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "Starting Streamlit server..." -ForegroundColor Cyan
Write-Host "📍 Server will be at: Screenshot (63).png
Screenshot (60).png
Screenshot (61).png
Screenshot (62).pnghttp://127.0.0.1:8501" -ForegroundColor Yellow
Write-Host "⏳ Please wait 10-15 seconds for the app to start..." -ForegroundColor Yellow
Write-Host ""

# Start the app
python -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501

