# Instalar Modelos de IA - Sistema de Auditoria Fiscal
# Script para usuário final

Write-Host "🤖 INSTALANDO MODELOS DE INTELIGÊNCIA ARTIFICIAL..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Verificar se Ollama está instalado
if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Ollama não encontrado!" -ForegroundColor Red
    Write-Host "📥 Baixe em: https://ollama.ai/download" -ForegroundColor Yellow
    Write-Host "💡 Instale o Ollama e execute este script novamente" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Ollama encontrado" -ForegroundColor Green

# Verificar se Ollama está rodando
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3
    Write-Host "✅ Ollama funcionando (versão $($response.version))" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Ollama não está respondendo" -ForegroundColor Yellow
    Write-Host "🔄 Tentando iniciar Ollama..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "📥 BAIXANDO MODELOS DE IA..." -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "⏳ ATENÇÃO: Este processo pode demorar 20-60 minutos" -ForegroundColor Yellow
Write-Host "💾 Os modelos ocupam cerca de 10-15GB de espaço" -ForegroundColor Yellow
Write-Host ""

# Lista de modelos essenciais
$modelos = @(
    @{nome="llama3.1:8b"; descricao="Modelo principal (4.7GB)"; essencial=$true},
    @{nome="mistral:7b"; descricao="Modelo alternativo (4.1GB)"; essencial=$true},
    @{nome="codellama:7b"; descricao="Para análise de código (3.8GB)"; essencial=$false},
    @{nome="gemma2:9b"; descricao="Modelo adicional (5.4GB)"; essencial=$false}
)

# Verificar modelos já instalados
Write-Host "🔍 Verificando modelos já instalados..." -ForegroundColor Yellow
$modelosInstalados = ollama list

foreach ($modelo in $modelos) {
    $nomeModelo = $modelo.nome
    $descricao = $modelo.descricao
    $essencial = $modelo.essencial

    if ($modelosInstalados -like "*$nomeModelo*") {
        Write-Host "✅ $nomeModelo já instalado" -ForegroundColor Green
    } else {
        if ($essencial) {
            Write-Host "📥 Baixando $nomeModelo - $descricao" -ForegroundColor Cyan
            Write-Host "⏳ Aguarde..." -ForegroundColor Yellow
            ollama pull $nomeModelo
            Write-Host "✅ $nomeModelo instalado" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $nomeModelo ($descricao) - OPCIONAL" -ForegroundColor Yellow
            $resposta = Read-Host "Deseja instalar? (s/N)"
            if ($resposta -eq "s" -or $resposta -eq "S") {
                Write-Host "📥 Baixando $nomeModelo..." -ForegroundColor Cyan
                ollama pull $nomeModelo
                Write-Host "✅ $nomeModelo instalado" -ForegroundColor Green
            } else {
                Write-Host "⏭️ Pulando $nomeModelo" -ForegroundColor Gray
            }
        }
    }
    Write-Host ""
}

# Testar um modelo
Write-Host "🧪 TESTANDO INTELIGÊNCIA ARTIFICIAL..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

try {
    Write-Host "💭 Fazendo pergunta teste para o modelo..." -ForegroundColor Yellow
    $teste = ollama run llama3.1:8b "Olá! Responda apenas: IA funcionando"
    if ($teste -like "*funcionando*" -or $teste -like "*funciona*") {
        Write-Host "✅ IA respondeu corretamente!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ IA respondeu: $teste" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erro ao testar IA" -ForegroundColor Red
}

# Listar modelos finais
Write-Host ""
Write-Host "📋 MODELOS INSTALADOS:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
ollama list

Write-Host ""
Write-Host "🎉 INTELIGÊNCIA ARTIFICIAL CONFIGURADA!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "💡 FUNCIONALIDADES DISPONÍVEIS:" -ForegroundColor Yellow
Write-Host "• Classificação automática de produtos" -ForegroundColor White
Write-Host "• Análise de conformidade fiscal" -ForegroundColor White
Write-Host "• Sugestões de otimização" -ForegroundColor White
Write-Host "• Chatbot para dúvidas" -ForegroundColor White
Write-Host ""
Write-Host "🌐 A IA estará disponível em: http://localhost:11434" -ForegroundColor White
Write-Host ""

pause
