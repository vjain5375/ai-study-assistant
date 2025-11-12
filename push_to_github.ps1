# Script to push to GitHub
# Usage: .\push_to_github.ps1 YOUR_GITHUB_USERNAME REPO_NAME

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "ai-study-assistant"
)

Write-Host "🚀 Setting up GitHub repository..." -ForegroundColor Green
Write-Host ""

# Check if remote already exists
$remoteExists = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Remote 'origin' already exists. Removing..." -ForegroundColor Yellow
    git remote remove origin
}

# Add remote
$repoUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "📦 Adding remote: $repoUrl" -ForegroundColor Cyan
git remote add origin $repoUrl

# Rename branch to main
Write-Host "🔄 Renaming branch to 'main'..." -ForegroundColor Cyan
git branch -M main

# Push to GitHub
Write-Host "⬆️  Pushing to GitHub..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  You may be prompted for GitHub credentials." -ForegroundColor Yellow
Write-Host "   Use a Personal Access Token (not password) if 2FA is enabled." -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "🌐 Repository: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "   1. Repository doesn't exist on GitHub - create it first at https://github.com/new" -ForegroundColor Yellow
    Write-Host "   2. Authentication failed - use Personal Access Token" -ForegroundColor Yellow
    Write-Host "   3. Check your internet connection" -ForegroundColor Yellow
}

