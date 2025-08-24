# Iniciar Backend - Sistema de Auditoria Fiscal
# Script simplificado para usuario final

Write-Host "INICIANDO BACKEND DO SISTEMA..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Verificar se estamos na pasta correta
if (-not (Test-Path "microservices\gateway\main.py")) {
    Write-Host "Execute este script na pasta raiz do sistema!" -ForegroundColor Red
    Write-Host "Navegue para a pasta onde estao os arquivos do sistema" -ForegroundColor Yellow
    pause
    exit 1
}

# Ativar ambiente conda
Write-Host "Ativando ambiente Python..." -ForegroundColor Yellow
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Configurar variaveis de ambiente
Write-Host "Configurando sistema..." -ForegroundColor Yellow
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"
$env:PYTHONPATH=$PWD

Write-Host "Configuracao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "Iniciando API Gateway..." -ForegroundColor Cyan
Write-Host "O backend estara disponivel em: http://localhost:8000" -ForegroundColor White
Write-Host "Documentacao da API em: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "MANTENHA ESTA JANELA ABERTA" -ForegroundColor Yellow
Write-Host "Para parar: Pressione Ctrl+C" -ForegroundColor Gray
Write-Host ""

# Iniciar API Gateway
cd microservices\gateway
python main.py
