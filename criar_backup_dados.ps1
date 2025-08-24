# Criar Backup dos Dados - Sistema de Auditoria Fiscal
# Script para usuário final

Write-Host "💾 BACKUP DO SISTEMA DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Criar pasta de backup com data/hora
$dataHora = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$pastaBackup = "backups\backup_$dataHora"

Write-Host "📁 Criando pasta de backup: $pastaBackup" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $pastaBackup -Force | Out-Null

# Backup do banco PostgreSQL
Write-Host ""
Write-Host "💾 Fazendo backup do banco de dados..." -ForegroundColor Cyan

try {
    # Verificar se container PostgreSQL está rodando
    $postgresStatus = docker inspect --format='{{.State.Status}}' auditoria_postgres 2>$null
    if ($postgresStatus -eq "running") {
        Write-Host "📊 Exportando dados do PostgreSQL..." -ForegroundColor Yellow
        docker exec auditoria_postgres pg_dump -U auditoria_user auditoria_fiscal_local > "$pastaBackup\banco_dados.sql"
        Write-Host "✅ Backup do banco concluído" -ForegroundColor Green
    } else {
        Write-Host "⚠️ PostgreSQL não está rodando - backup do banco ignorado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erro no backup do banco de dados" -ForegroundColor Red
}

# Backup dos arquivos de configuração
Write-Host ""
Write-Host "⚙️ Fazendo backup das configurações..." -ForegroundColor Cyan

$arquivosConfig = @(
    ".env",
    "config.py",
    "requirements.txt"
)

foreach ($arquivo in $arquivosConfig) {
    if (Test-Path $arquivo) {
        Copy-Item $arquivo "$pastaBackup\" -Force
        Write-Host "✅ $arquivo copiado" -ForegroundColor Green
    }
}

# Backup dos logs
Write-Host ""
Write-Host "📝 Fazendo backup dos logs..." -ForegroundColor Cyan

if (Test-Path "logs") {
    Copy-Item "logs" "$pastaBackup\logs" -Recurse -Force
    Write-Host "✅ Logs copiados" -ForegroundColor Green
} else {
    Write-Host "⚠️ Pasta de logs não encontrada" -ForegroundColor Yellow
}

# Backup dos dados uploaded
Write-Host ""
Write-Host "📄 Fazendo backup dos arquivos enviados..." -ForegroundColor Cyan

if (Test-Path "data\uploads") {
    Copy-Item "data\uploads" "$pastaBackup\uploads" -Recurse -Force
    Write-Host "✅ Arquivos enviados copiados" -ForegroundColor Green
} else {
    Write-Host "⚠️ Pasta de uploads não encontrada" -ForegroundColor Yellow
}

# Backup das configurações do frontend
Write-Host ""
Write-Host "🎨 Fazendo backup das configurações do frontend..." -ForegroundColor Cyan

if (Test-Path "frontend\package.json") {
    Copy-Item "frontend\package.json" "$pastaBackup\" -Force
    Write-Host "✅ Configurações do frontend copiadas" -ForegroundColor Green
}

# Criar arquivo de informações do backup
Write-Host ""
Write-Host "📋 Criando arquivo de informações..." -ForegroundColor Cyan

$infoBackup = @"
BACKUP DO SISTEMA DE AUDITORIA FISCAL
====================================

Data/Hora: $(Get-Date)
Versão: v4.0
Sistema: Windows 11

CONTEÚDO DO BACKUP:
- banco_dados.sql: Backup completo do PostgreSQL
- logs/: Todos os logs do sistema
- uploads/: Arquivos enviados pelos usuários
- .env: Configurações do ambiente
- config.py: Configurações do sistema
- requirements.txt: Dependências Python
- package.json: Configurações do frontend

COMO RESTAURAR:
1. Restaurar banco: docker exec -i auditoria_postgres psql -U auditoria_user auditoria_fiscal_local < banco_dados.sql
2. Copiar arquivos de volta para as pastas originais
3. Reiniciar o sistema

OBSERVAÇÕES:
- Este backup NÃO inclui os modelos de IA (Ollama)
- Para backup completo dos modelos IA, use: ollama list e ollama export
- Mantenha múltiplos backups para segurança

SISTEMA DE AUDITORIA FISCAL v4.0
Data do backup: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")
"@

$infoBackup | Out-File -FilePath "$pastaBackup\INFO_BACKUP.txt" -Encoding UTF8

# Calcular tamanho do backup
$tamanhoBackup = (Get-ChildItem $pastaBackup -Recurse | Measure-Object -Property Length -Sum).Sum
$tamanhoMB = [math]::Round($tamanhoBackup / 1MB, 2)

Write-Host ""
Write-Host "🎉 BACKUP CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host "📁 Local: $pastaBackup" -ForegroundColor White
Write-Host "📊 Tamanho: $tamanhoMB MB" -ForegroundColor White
Write-Host "📅 Data: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor White
Write-Host ""
Write-Host "💡 DICAS IMPORTANTES:" -ForegroundColor Yellow
Write-Host "• Mantenha pelo menos 3 backups diferentes" -ForegroundColor White
Write-Host "• Teste a restauração periodicamente" -ForegroundColor White
Write-Host "• Guarde cópias em local seguro (nuvem/HD externo)" -ForegroundColor White
Write-Host "• Faça backup semanalmente" -ForegroundColor White
Write-Host ""
Write-Host "📋 Para listar todos os backups: Get-ChildItem backups\" -ForegroundColor Gray

pause
