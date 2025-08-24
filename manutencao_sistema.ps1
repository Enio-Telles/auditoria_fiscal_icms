# Manutenção do Sistema - Sistema de Auditoria Fiscal
# Script para usuário final manter o sistema funcionando bem

Write-Host "🛠️ MANUTENÇÃO DO SISTEMA DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

$dataManutencao = Get-Date
Write-Host "📅 Iniciando manutenção em: $dataManutencao" -ForegroundColor White
Write-Host ""

# 1. Verificar status geral
Write-Host "🔍 1. VERIFICANDO STATUS GERAL..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✅ Docker: Disponível" -ForegroundColor Green
    try {
        docker version | Out-Null
        Write-Host "✅ Docker: Funcionando" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Docker: Não está rodando" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Docker: Não instalado" -ForegroundColor Red
}

# Python/Conda
if (Get-Command conda -ErrorAction SilentlyContinue) {
    Write-Host "✅ Python/Anaconda: Disponível" -ForegroundColor Green
} else {
    Write-Host "❌ Python/Anaconda: Não encontrado" -ForegroundColor Red
}

# Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "✅ Node.js: Disponível" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js: Não encontrado" -ForegroundColor Red
}

# 2. Limpar arquivos temporários
Write-Host ""
Write-Host "🧹 2. LIMPANDO ARQUIVOS TEMPORÁRIOS..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$arquivosLimpos = 0

# Cache Python
Get-ChildItem -Path . -Recurse -Name "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
    $arquivosLimpos++
}

# Logs antigos (mais de 30 dias)
if (Test-Path "logs") {
    Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | ForEach-Object {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        $arquivosLimpos++
    }
}

# Arquivos temporários
if (Test-Path "data\temp") {
    Get-ChildItem "data\temp\*" -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        $arquivosLimpos++
    }
}

Write-Host "✅ $arquivosLimpos arquivos/pastas temporários removidos" -ForegroundColor Green

# 3. Verificar espaço em disco
Write-Host ""
Write-Host "💾 3. VERIFICANDO ESPAÇO EM DISCO..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

$discos = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3}
foreach ($disco in $discos) {
    $espacoLivreGB = [math]::Round($disco.FreeSpace/1GB, 2)
    $espacoTotalGB = [math]::Round($disco.Size/1GB, 2)
    $percentualLivre = [math]::Round(($disco.FreeSpace/$disco.Size)*100, 1)

    Write-Host "💾 Disco $($disco.DeviceID) - $espacoLivreGB GB livre de $espacoTotalGB GB ($percentualLivre%)" -ForegroundColor White

    if ($percentualLivre -lt 10) {
        Write-Host "⚠️ ATENÇÃO: Pouco espaço livre no disco $($disco.DeviceID)!" -ForegroundColor Red
    } elseif ($percentualLivre -lt 20) {
        Write-Host "⚠️ Aviso: Espaço limitado no disco $($disco.DeviceID)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Espaço adequado no disco $($disco.DeviceID)" -ForegroundColor Green
    }
}

# 4. Verificar containers Docker
Write-Host ""
Write-Host "🐳 4. VERIFICANDO CONTAINERS DOCKER..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

try {
    $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}" | findstr auditoria
    if ($containers) {
        Write-Host $containers

        # Verificar containers não utilizados
        $containersParados = docker ps -a --filter "status=exited" --format "{{.Names}}" | findstr auditoria
        if ($containersParados) {
            Write-Host ""
            Write-Host "🗑️ Containers parados encontrados:" -ForegroundColor Yellow
            $containersParados | ForEach-Object { Write-Host "• $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "⚠️ Nenhum container do sistema encontrado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erro ao verificar containers" -ForegroundColor Red
}

# 5. Verificar logs de erro
Write-Host ""
Write-Host "📝 5. VERIFICANDO LOGS DE ERRO..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$errosEncontrados = 0

if (Test-Path "logs") {
    $arquivosLog = Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue
    foreach ($logFile in $arquivosLog) {
        $erros = Select-String -Path $logFile.FullName -Pattern "ERROR|CRITICAL|FATAL" -ErrorAction SilentlyContinue
        if ($erros) {
            $errosEncontrados += $erros.Count
        }
    }
}

if ($errosEncontrados -gt 0) {
    Write-Host "⚠️ $errosEncontrados erros encontrados nos logs" -ForegroundColor Yellow
    Write-Host "💡 Verifique os arquivos em logs\ para detalhes" -ForegroundColor Gray
} else {
    Write-Host "✅ Nenhum erro crítico encontrado nos logs" -ForegroundColor Green
}

# 6. Verificar conexões de rede
Write-Host ""
Write-Host "🌐 6. VERIFICANDO CONEXÕES DE REDE..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$portas = @(
    @{porta=3001; servico="Frontend React"},
    @{porta=8000; servico="Backend API"},
    @{porta=5432; servico="PostgreSQL"},
    @{porta=6379; servico="Redis"},
    @{porta=11434; servico="Ollama IA"}
)

foreach ($item in $portas) {
    $conexao = netstat -an | findstr ":$($item.porta)"
    if ($conexao) {
        Write-Host "✅ Porta $($item.porta) ($($item.servico)): Em uso" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Porta $($item.porta) ($($item.servico)): Não está em uso" -ForegroundColor Yellow
    }
}

# 7. Otimização de performance
Write-Host ""
Write-Host "⚡ 7. OTIMIZAÇÃO DE PERFORMANCE..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Verificar uso de memória
$memoriaTotal = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory
$memoriaLivre = (Get-WmiObject -Class Win32_OperatingSystem).FreePhysicalMemory * 1024
$memoriaUsada = $memoriaTotal - $memoriaLivre
$percentualUso = [math]::Round(($memoriaUsada / $memoriaTotal) * 100, 1)

Write-Host "🧠 Uso de memória: $percentualUso%" -ForegroundColor White

if ($percentualUso -gt 90) {
    Write-Host "⚠️ ATENÇÃO: Uso alto de memória!" -ForegroundColor Red
    Write-Host "💡 Considere fechar programas desnecessários" -ForegroundColor Yellow
} elseif ($percentualUso -gt 75) {
    Write-Host "⚠️ Uso moderado de memória" -ForegroundColor Yellow
} else {
    Write-Host "✅ Uso normal de memória" -ForegroundColor Green
}

# 8. Criar relatório de manutenção
Write-Host ""
Write-Host "📋 8. CRIANDO RELATÓRIO DE MANUTENÇÃO..." -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

$relatorio = @"
RELATÓRIO DE MANUTENÇÃO - SISTEMA DE AUDITORIA FISCAL
=====================================================

Data/Hora: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")
Versão: v4.0

RESUMO DA MANUTENÇÃO:
• Arquivos temporários removidos: $arquivosLimpos
• Erros encontrados nos logs: $errosEncontrados
• Uso de memória: $percentualUso%

VERIFICAÇÕES REALIZADAS:
✓ Status dos programas necessários
✓ Limpeza de arquivos temporários
✓ Verificação de espaço em disco
✓ Status dos containers Docker
✓ Análise de logs de erro
✓ Verificação de portas de rede
✓ Análise de performance

RECOMENDAÇÕES:
$(if ($percentualUso -gt 75) { "• Monitorar uso de memória`n" })
$(if ($errosEncontrados -gt 0) { "• Investigar erros nos logs`n" })
• Executar manutenção semanalmente
• Fazer backup dos dados regularmente
• Manter o sistema atualizado

PRÓXIMA MANUTENÇÃO SUGERIDA: $(Get-Date (Get-Date).AddDays(7) -Format "dd/MM/yyyy")

Sistema de Auditoria Fiscal v4.0
Manutenção automática concluída
"@

New-Item -ItemType Directory -Path "logs" -Force | Out-Null
$relatorio | Out-File -FilePath "logs\manutencao_$(Get-Date -Format 'yyyy-MM-dd').txt" -Encoding UTF8

Write-Host "✅ Relatório salvo em: logs\manutencao_$(Get-Date -Format 'yyyy-MM-dd').txt" -ForegroundColor Green

# Finalização
Write-Host ""
Write-Host "🎉 MANUTENÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 RESUMO:" -ForegroundColor Cyan
Write-Host "• Duração: $((Get-Date) - $dataManutencao | ForEach-Object {'{0:mm}:{0:ss}' -f $_})" -ForegroundColor White
Write-Host "• Arquivos limpos: $arquivosLimpos" -ForegroundColor White
Write-Host "• Erros encontrados: $errosEncontrados" -ForegroundColor White
Write-Host "• Uso de memória: $percentualUso%" -ForegroundColor White
Write-Host ""
Write-Host "📅 Próxima manutenção recomendada: $(Get-Date (Get-Date).AddDays(7) -Format 'dd/MM/yyyy')" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 DICAS:" -ForegroundColor Gray
Write-Host "• Execute este script semanalmente" -ForegroundColor White
Write-Host "• Faça backup antes de grandes atualizações" -ForegroundColor White
Write-Host "• Monitore os logs regularmente" -ForegroundColor White

pause
