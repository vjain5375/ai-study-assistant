# Setup script to create .env file with API keys
# Run this script: .\setup_env.ps1

$envContent = @"
# Multi-Provider API Keys Configuration
# ======================================

# Google Gemini API Key (Required for Reader Agent)
GEMINI_API_KEY=your_gemini_api_key_here

# Groq API Key (Required for Flashcard & Planner Agents)
GROQ_API_KEY=your_groq_api_key_here

# DeepSeek API Key (Required for Quiz & Chat Agents)
# Get your API key at: https://platform.deepseek.com/
DEEPSEEK_API_KEY=

# Optional: Fallback to OpenAI (if other providers not available)
# OPENAI_API_KEY=
"@

$envContent | Out-File -FilePath ".env" -Encoding utf8
Write-Host "✅ .env file created successfully!" -ForegroundColor Green
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Get DeepSeek API key from: https://platform.deepseek.com/" -ForegroundColor Yellow
Write-Host "   2. Add DEEPSEEK_API_KEY to .env file" -ForegroundColor Yellow
Write-Host "   3. Install dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
Write-Host "   4. Run the app: python main.py" -ForegroundColor Yellow

