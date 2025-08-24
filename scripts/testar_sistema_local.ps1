# 🧪 Script de Teste Local Windows 11
# Sistema de Auditoria Fiscal ICMS v4.0

Write-Host "🧪 TESTANDO SISTEMA LOCAL WINDOWS 11..." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Função para testar endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$ExpectedStatus = 200,
        [int]$Timeout = 10
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $Timeout -UseBasicParsing
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✅ $Name (HTTP $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  $Name (HTTP $($response.StatusCode), esperado $ExpectedStatus)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ $Name (Erro: $($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Função para testar comando Docker
function Test-DockerContainer {
    param(
        [string]$ContainerName,
        [string]$TestCommand,
        [string]$Description
    )

    try {
        $result = docker exec $ContainerName $TestCommand 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $Description (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $Description (Erro: $($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

$totalTests = 0
$passedTests = 0

Write-Host "🐳 1. TESTANDO CONTAINERS DOCKER..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

# Verificar se containers estão rodando
$containers = @("auditoria-postgres-local", "auditoria-redis-local", "auditoria-ollama-local")

foreach ($container in $containers) {
    $totalTests++
    $status = docker inspect --format='{{.State.Status}}' $container 2>$null
    if ($status -eq "running") {
        Write-Host "✅ Container $container rodando" -ForegroundColor Green
        $passedTests++
    } else {
        Write-Host "❌ Container $container não está rodando (Status: $status)" -ForegroundColor Red
    }
}

# Testar conectividade dos containers
Write-Host ""
Write-Host "💾 2. TESTANDO SERVIÇOS DE DADOS..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

# PostgreSQL
$totalTests++
if (Test-DockerContainer "auditoria-postgres-local" "pg_isready -U auditoria_user" "PostgreSQL conectividade") {
    $passedTests++
}

# Redis
$totalTests++
if (Test-DockerContainer "auditoria-redis-local" "redis-cli ping" "Redis conectividade") {
    $passedTests++
}

# Ollama
$totalTests++
if (Test-Endpoint "http://localhost:11434/api/version" "Ollama API" 200 5) {
    $passedTests++

    # Testar modelos Ollama
    try {
        $models = docker exec auditoria-ollama-local ollama list 2>$null
        if ($models -and $models.Length -gt 1) {
            Write-Host "✅ Modelos Ollama carregados" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Nenhum modelo Ollama carregado" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Erro ao verificar modelos Ollama" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🌐 3. TESTANDO APIS DO SISTEMA..." -ForegroundColor Cyan
Write-Host "---------------------------------"

# API Gateway
$totalTests++
if (Test-Endpoint "http://localhost:8000/health" "API Gateway Health" 200 5) {
    $passedTests++
}

$totalTests++
if (Test-Endpoint "http://localhost:8000/docs" "API Documentation" 200 5) {
    $passedTests++
}

# Testar endpoints específicos
$endpoints = @(
    @{Url="http://localhost:8001/health"; Name="Auth Service"},
    @{Url="http://localhost:8002/health"; Name="Tenant Service"},
    @{Url="http://localhost:8003/health"; Name="Product Service"},
    @{Url="http://localhost:8004/health"; Name="Classification Service"},
    @{Url="http://localhost:8005/health"; Name="Import Service"},
    @{Url="http://localhost:8006/health"; Name="AI Service"}
)

foreach ($endpoint in $endpoints) {
    $totalTests++
    if (Test-Endpoint $endpoint.Url $endpoint.Name 200 3) {
        $passedTests++
    }
}

Write-Host ""
Write-Host "🎨 4. TESTANDO FRONTEND..." -ForegroundColor Cyan
Write-Host "-------------------------"

$totalTests++
if (Test-Endpoint "http://localhost:3000" "React Frontend" 200 10) {
    $passedTests++

    # Verificar se é uma aplicação React
    try {
        $frontendContent = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        if ($frontendContent.Content -like "*react*" -or $frontendContent.Content -like "*React*") {
            Write-Host "✅ Aplicação React detectada" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Conteúdo React não detectado" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Erro ao verificar conteúdo React" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🧠 5. TESTANDO SISTEMA DE IA..." -ForegroundColor Cyan
Write-Host "-------------------------------"

# Teste básico de classificação
$totalTests++
try {
    $classificationTest = @{
        description = "Notebook Dell Inspiron i7"
        category = "informatica"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8004/classify" -Method POST -Body $classificationTest -ContentType "application/json" -TimeoutSec 10

    if ($response) {
        Write-Host "✅ Sistema de classificação funcionando" -ForegroundColor Green
        $passedTests++

        if ($response.ncm -or $response.classification) {
            Write-Host "✅ Classificação retornou dados válidos" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Classificação sem dados específicos" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Sistema de classificação não respondeu" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Sistema de classificação com erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 6. TESTANDO INTEGRAÇÃO COMPLETA..." -ForegroundColor Cyan
Write-Host "-------------------------------------"

# Teste de fluxo completo
$totalTests++
try {
    # 1. Testar login (simulado)
    $loginData = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8001/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 5 -ErrorAction SilentlyContinue

    if ($loginResponse -and $loginResponse.access_token) {
        Write-Host "✅ Sistema de autenticação funcionando" -ForegroundColor Green
        $passedTests++

        # 2. Testar endpoint protegido
        $headers = @{
            Authorization = "Bearer $($loginResponse.access_token)"
        }

        $protectedResponse = Invoke-RestMethod -Uri "http://localhost:8002/tenants/" -Headers $headers -TimeoutSec 5 -ErrorAction SilentlyContinue

        if ($protectedResponse) {
            Write-Host "✅ Autenticação JWT funcionando" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Endpoint protegido não respondeu" -ForegroundColor Yellow
        }

    } else {
        Write-Host "⚠️  Sistema de autenticação não configurado ou usuário não existe" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Teste de integração: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 7. TESTANDO PERFORMANCE..." -ForegroundColor Cyan
Write-Host "-----------------------------"

# Verificar uso de recursos
try {
    Write-Host "💻 Uso de recursos dos containers:"
    $stats = docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | Where-Object { $_ -like "*auditoria*" }
    $stats | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} catch {
    Write-Host "⚠️  Erro ao obter estatísticas dos containers" -ForegroundColor Yellow
}

# Verificar portas em uso
Write-Host ""
Write-Host "🌐 Portas do sistema em uso:"
$ports = @(3000, 5432, 6379, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 11434)
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "   ✅ Porta $port ativa" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Porta $port inativa" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "📋 RESULTADO DOS TESTES" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Total de testes: $totalTests" -ForegroundColor White
Write-Host "Testes passaram: $passedTests" -ForegroundColor Green
Write-Host "Testes falharam: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "Taxa de sucesso: $successRate%" -ForegroundColor Cyan

Write-Host ""

if ($successRate -ge 80) {
    Write-Host "🎉 SISTEMA FUNCIONANDO EXCELENTE!" -ForegroundColor Green
    Write-Host "O sistema está pronto para uso." -ForegroundColor Green
} elseif ($successRate -ge 60) {
    Write-Host "⚠️  SISTEMA FUNCIONANDO COM PROBLEMAS MENORES" -ForegroundColor Yellow
    Write-Host "Alguns serviços podem precisar de ajustes." -ForegroundColor Yellow
} else {
    Write-Host "❌ SISTEMA COM PROBLEMAS SIGNIFICATIVOS" -ForegroundColor Red
    Write-Host "Vários serviços precisam ser corrigidos." -ForegroundColor Red
}

Write-Host ""
Write-Host "🔗 LINKS ÚTEIS:" -ForegroundColor Cyan
Write-Host "• Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "• API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "• Health Check: http://localhost:8000/health" -ForegroundColor White

Write-Host ""
Write-Host "📝 LOGS DETALHADOS:" -ForegroundColor Cyan
Write-Host "• API Gateway: docker logs auditoria-gateway-local --tail 20" -ForegroundColor White
Write-Host "• PostgreSQL: docker logs auditoria-postgres-local --tail 20" -ForegroundColor White
Write-Host "• Ollama: docker logs auditoria-ollama-local --tail 20" -ForegroundColor White

Write-Host ""
Write-Host "🎯 Teste concluído em $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor Gray
