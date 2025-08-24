# Teste simples do Docker - Windows 11

Write-Host "TESTANDO DOCKER..." -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""

# Verificar se Docker esta instalado
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker encontrado" -ForegroundColor Green
} else {
    Write-Host "Docker NAO encontrado!" -ForegroundColor Red
    Write-Host "Instale Docker Desktop primeiro" -ForegroundColor Yellow
    exit 1
}

# Testar Docker
Write-Host "Testando conectividade..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Versao: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Erro ao obter versao" -ForegroundColor Red
}

try {
    docker info | Out-Null
    Write-Host "Docker esta FUNCIONANDO!" -ForegroundColor Green

    # Testar comandos basicos
    Write-Host ""
    Write-Host "Testando comandos basicos..." -ForegroundColor Yellow

    # Listar containers
    Write-Host "Containers existentes:"
    docker ps -a

    # Listar networks
    Write-Host ""
    Write-Host "Networks existentes:"
    docker network ls

    Write-Host ""
    Write-Host "Docker esta pronto para uso!" -ForegroundColor Green
    Write-Host "Execute: .\start_sistema_local.ps1" -ForegroundColor Cyan

} catch {
    Write-Host "Docker NAO esta respondendo!" -ForegroundColor Red
    Write-Host ""
    Write-Host "SOLUCOES:" -ForegroundColor Yellow
    Write-Host "1. Abra Docker Desktop do menu Iniciar" -ForegroundColor White
    Write-Host "2. Aguarde 1-2 minutos para inicializar" -ForegroundColor White
    Write-Host "3. Verifique o icone na bandeja do sistema" -ForegroundColor White
    Write-Host "4. Execute este teste novamente" -ForegroundColor White
}
