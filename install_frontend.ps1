# PowerShell script to install frontend dependencies
Set-Location -Path "C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms\frontend"

Write-Host "Starting Frontend Installation..." -ForegroundColor Green
Write-Host "Current Directory: $(Get-Location)" -ForegroundColor Yellow

# Check if package.json exists
if (Test-Path "package.json") {
    Write-Host "package.json found" -ForegroundColor Green
} else {
    Write-Host "package.json not found!" -ForegroundColor Red
    exit 1
}

# Clean previous installations
Write-Host "Cleaning previous installations..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules"
    Write-Host "   Removed node_modules" -ForegroundColor Gray
}
if (Test-Path "package-lock.json") {
    Remove-Item -Force "package-lock.json"
    Write-Host "   Removed package-lock.json" -ForegroundColor Gray
}
if (Test-Path "yarn.lock") {
    Remove-Item -Force "yarn.lock"
    Write-Host "   Removed yarn.lock" -ForegroundColor Gray
}

# Clean npm cache
Write-Host "Cleaning npm cache..." -ForegroundColor Yellow
npm cache clean --force

# Try multiple installation approaches
Write-Host "Attempting installation with npm..." -ForegroundColor Yellow

# Approach 1: npm with force
Write-Host "   Trying: npm install --force" -ForegroundColor Gray
npm install --force
if ($LASTEXITCODE -eq 0) {
    Write-Host "npm install --force succeeded!" -ForegroundColor Green
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    exit 0
}

# Approach 2: npm with legacy peer deps
Write-Host "   Trying: npm install --legacy-peer-deps" -ForegroundColor Gray
npm install --legacy-peer-deps
if ($LASTEXITCODE -eq 0) {
    Write-Host "npm install --legacy-peer-deps succeeded!" -ForegroundColor Green
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    exit 0
}

# Approach 3: yarn
Write-Host "   Trying: yarn install" -ForegroundColor Gray
yarn install
if ($LASTEXITCODE -eq 0) {
    Write-Host "yarn install succeeded!" -ForegroundColor Green
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    exit 0
}

Write-Host "All installation attempts failed!" -ForegroundColor Red
Write-Host "Manual steps required:" -ForegroundColor Yellow
Write-Host "   1. cd frontend" -ForegroundColor Gray
Write-Host "   2. npm install --force" -ForegroundColor Gray
Write-Host "   3. npm start" -ForegroundColor Gray
