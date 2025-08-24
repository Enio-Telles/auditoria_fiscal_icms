# Iniciar Frontend - Sistema de Auditoria Fiscal
# Script simplificado para usuário final

Write-Host "🎨 INICIANDO INTERFACE DO SISTEMA..." -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# Verificar se a pasta frontend existe
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Pasta frontend não encontrada!" -ForegroundColor Red
    Write-Host "📁 Execute este script na pasta raiz do sistema" -ForegroundColor Yellow
    pause
    exit 1
}

# Navegar para pasta frontend
cd frontend

# Verificar se Node.js está instalado
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js não encontrado!" -ForegroundColor Red
    Write-Host "📥 Instale em: https://nodejs.org/" -ForegroundColor Yellow
    pause
    exit 1
}

# Configurar variável de ambiente
Write-Host "⚙️ Configurando interface..." -ForegroundColor Yellow
$env:REACT_APP_API_URL="http://localhost:8000"

# Verificar se dependências estão instaladas
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências da interface..." -ForegroundColor Yellow
    Write-Host "⏳ Isso pode demorar alguns minutos na primeira vez..." -ForegroundColor Gray
    npm install
}

Write-Host "✅ Configuração concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Iniciando interface web..." -ForegroundColor Cyan
Write-Host "🌐 A interface estará disponível em: http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "🔑 DADOS PARA LOGIN:" -ForegroundColor Yellow
Write-Host "Email: admin@demo.com" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "⚠️ MANTENHA ESTA JANELA ABERTA" -ForegroundColor Yellow
Write-Host "💡 Para parar: Pressione Ctrl+C" -ForegroundColor Gray
Write-Host "🌐 O navegador abrirá automaticamente" -ForegroundColor Gray
Write-Host ""

# Iniciar React
npm start
