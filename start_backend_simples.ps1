# Inicializar Backend Simplificado - Windows 11

Write-Host "INICIANDO BACKEND DO SISTEMA..." -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""

# Verificar se estamos na pasta correta
if (-not (Test-Path "microservices\gateway\main.py")) {
    Write-Host "Pasta incorreta! Execute na pasta raiz do projeto" -ForegroundColor Red
    exit 1
}

# Ativar ambiente conda
Write-Host "Ativando ambiente conda..." -ForegroundColor Yellow
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Configurar variaveis de ambiente
Write-Host "Configurando variaveis..." -ForegroundColor Yellow
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"
$env:PYTHONPATH=$PWD

Write-Host "Variaveis configuradas:" -ForegroundColor Green
Write-Host "- DATABASE_URL: $env:DATABASE_URL" -ForegroundColor Gray
Write-Host "- REDIS_URL: $env:REDIS_URL" -ForegroundColor Gray
Write-Host "- OLLAMA_URL: $env:OLLAMA_URL" -ForegroundColor Gray

Write-Host ""
Write-Host "Iniciando API Gateway na porta 8000..." -ForegroundColor Cyan
Write-Host "======================================"
cd microservices\gateway
python main.py
