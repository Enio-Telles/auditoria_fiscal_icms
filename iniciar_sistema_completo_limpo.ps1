# Iniciar Sistema Completo - Sistema de Auditoria Fiscal
# Script para iniciar todos os componentes do sistema de uma so vez

Write-Host "INICIANDO SISTEMA COMPLETO DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

$inicioExecucao = Get-Date
$errosEncontrados = 0

# Verificar se estamos na pasta correta
if (-not (Test-Path "config.py")) {
    Write-Host "ERRO: Execute este script na pasta raiz do projeto!" -ForegroundColor Red
    Write-Host "Pasta atual: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "Pasta esperada: contendo config.py" -ForegroundColor Yellow
    pause
    exit 1
}

# Funcao para verificar se uma porta esta em uso
function Test-Port {
    param($porta)
    $conexao = netstat -an | findstr ":$porta "
    return $conexao -ne $null
}

# Funcao para aguardar servico ficar disponivel
function Wait-ForService {
    param($porta, $nomeServico, $tempoLimite = 60)
    
    Write-Host "Aguardando $nomeServico ficar disponivel..." -ForegroundColor Yellow
    $tempoInicio = Get-Date
    
    do {
        Start-Sleep -Seconds 2
        $disponivel = Test-Port $porta
        $tempoDecorrido = (Get-Date) - $tempoInicio
        
        if ($tempoDecorrido.TotalSeconds -gt $tempoLimite) {
            Write-Host "Timeout aguardando $nomeServico" -ForegroundColor Yellow
            return $false
        }
    } while (-not $disponivel)
    
    Write-Host "$nomeServico disponivel!" -ForegroundColor Green
    return $true
}

Write-Host "1. VERIFICACAO INICIAL..." -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Verificar Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker nao encontrado!" -ForegroundColor Red
    Write-Host "Instale o Docker Desktop e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

# Verificar Conda
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Anaconda/Conda nao encontrado!" -ForegroundColor Red
    Write-Host "Instale o Anaconda e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

# Verificar Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js nao encontrado!" -ForegroundColor Red
    Write-Host "Instale o Node.js e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

if ($errosEncontrados -gt 0) {
    Write-Host ""
    Write-Host "$errosEncontrados erro(s) encontrado(s)!" -ForegroundColor Red
    Write-Host "Corrija os problemas acima antes de continuar" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Todas as dependencias encontradas!" -ForegroundColor Green
Write-Host ""

Write-Host "2. INICIANDO SERVICOS BASE..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Verificar se Docker esta rodando
try {
    docker version | Out-Null
    Write-Host "Docker esta funcionando" -ForegroundColor Green
} catch {
    Write-Host "Docker nao esta rodando!" -ForegroundColor Red
    Write-Host "Inicie o Docker Desktop e tente novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Iniciar PostgreSQL se nao estiver rodando
if (-not (Test-Port 5432)) {
    Write-Host "Iniciando PostgreSQL..." -ForegroundColor Yellow
    
    # Verificar se ja existe um container PostgreSQL
    $postgresContainer = docker ps -a --filter "name=postgres_auditoria" --format "{{.Names}}"
    
    if ($postgresContainer) {
        Write-Host "Container PostgreSQL encontrado, iniciando..." -ForegroundColor Yellow
        docker start postgres_auditoria
    } else {
        Write-Host "Criando novo container PostgreSQL..." -ForegroundColor Yellow
        docker run -d --name postgres_auditoria `
            -e POSTGRES_DB=auditoria_fiscal `
            -e POSTGRES_USER=postgres `
            -e POSTGRES_PASSWORD=postgres123 `
            -p 5432:5432 `
            postgres:13
    }
    
    # Aguardar PostgreSQL ficar disponivel
    if (-not (Wait-ForService 5432 "PostgreSQL")) {
        Write-Host "Falha ao iniciar PostgreSQL" -ForegroundColor Red
        $errosEncontrados++
    }
} else {
    Write-Host "PostgreSQL ja esta rodando" -ForegroundColor Green
}

# Iniciar Redis se nao estiver rodando
if (-not (Test-Port 6379)) {
    Write-Host "Iniciando Redis..." -ForegroundColor Yellow
    
    # Verificar se ja existe um container Redis
    $redisContainer = docker ps -a --filter "name=redis_auditoria" --format "{{.Names}}"
    
    if ($redisContainer) {
        Write-Host "Container Redis encontrado, iniciando..." -ForegroundColor Yellow
        docker start redis_auditoria
    } else {
        Write-Host "Criando novo container Redis..." -ForegroundColor Yellow
        docker run -d --name redis_auditoria -p 6379:6379 redis:7-alpine
    }
    
    # Aguardar Redis ficar disponivel
    if (-not (Wait-ForService 6379 "Redis")) {
        Write-Host "Falha ao iniciar Redis" -ForegroundColor Red
        $errosEncontrados++
    }
} else {
    Write-Host "Redis ja esta rodando" -ForegroundColor Green
}

Write-Host ""
Write-Host "3. CONFIGURANDO AMBIENTE PYTHON..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Ativar ambiente conda
Write-Host "Ativando ambiente conda..." -ForegroundColor Yellow
try {
    conda activate auditoria-fiscal
    Write-Host "Ambiente conda ativado com sucesso" -ForegroundColor Green
} catch {
    Write-Host "Erro ao ativar ambiente conda" -ForegroundColor Red
    Write-Host "Execute: conda activate auditoria-fiscal" -ForegroundColor Yellow
    $errosEncontrados++
}

Write-Host ""
Write-Host "4. INICIANDO BACKEND..." -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Verificar se o backend ja esta rodando
if (Test-Port 8000) {
    Write-Host "Backend ja esta rodando na porta 8000" -ForegroundColor Green
} else {
    Write-Host "Iniciando API Gateway..." -ForegroundColor Yellow
    
    # Iniciar o backend em uma nova janela do PowerShell
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; conda activate auditoria-fiscal; python apis\api_estavel.py"
    
    # Aguardar o backend ficar disponivel
    if (Wait-ForService 8000 "API Gateway" 30) {
        Write-Host "Backend iniciado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "Timeout aguardando backend" -ForegroundColor Red
        $errosEncontrados++
    }
}

Write-Host ""
Write-Host "5. VERIFICANDO OLLAMA..." -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Verificar se Ollama esta rodando
if (Test-Port 11434) {
    Write-Host "Ollama ja esta rodando na porta 11434" -ForegroundColor Green
} else {
    Write-Host "Iniciando Ollama..." -ForegroundColor Yellow
    
    # Verificar se Ollama esta instalado
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        # Iniciar Ollama em background
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        
        # Aguardar Ollama ficar disponivel
        if (Wait-ForService 11434 "Ollama" 30) {
            Write-Host "Ollama iniciado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "Timeout aguardando Ollama" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Ollama nao encontrado, continuando sem IA local" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "6. INICIANDO FRONTEND..." -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Verificar se o frontend ja esta rodando
if (Test-Port 3001) {
    Write-Host "Frontend ja esta rodando na porta 3001" -ForegroundColor Green
} else {
    # Navegar para a pasta frontend
    if (Test-Path "frontend") {
        Write-Host "Navegando para pasta frontend..." -ForegroundColor Yellow
        Set-Location "frontend"
        
        # Verificar se node_modules existe
        if (-not (Test-Path "node_modules")) {
            Write-Host "Instalando dependencias do frontend..." -ForegroundColor Yellow
            npm install
        }
        
        # Criar arquivo .env.local se nao existir
        if (-not (Test-Path ".env.local")) {
            Write-Host "Criando arquivo .env.local..." -ForegroundColor Yellow
            @"
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=local
"@ | Out-File -FilePath ".env.local" -Encoding UTF8
        }
        
        # Iniciar servidor de desenvolvimento
        Write-Host "Iniciando servidor React..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm start"
        
        # Voltar para pasta raiz
        Set-Location ".."
        
        # Aguardar frontend ficar disponivel
        if (Wait-ForService 3001 "Frontend React" 60) {
            Write-Host "Frontend iniciado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "Timeout aguardando frontend" -ForegroundColor Red
            $errosEncontrados++
        }
    } else {
        Write-Host "Pasta frontend nao encontrada!" -ForegroundColor Red
        $errosEncontrados++
    }
}

Write-Host ""
Write-Host "RESUMO DA EXECUCAO" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

$tempoTotal = (Get-Date) - $inicioExecucao
Write-Host "Tempo total de execucao: $($tempoTotal.TotalSeconds) segundos" -ForegroundColor Gray

if ($errosEncontrados -eq 0) {
    Write-Host ""
    Write-Host "SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "=============================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Acesse o sistema em: http://localhost:3001" -ForegroundColor White
    Write-Host "API Gateway: http://localhost:8000" -ForegroundColor White
    Write-Host "Documentacao API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "Credenciais de acesso:" -ForegroundColor Yellow
    Write-Host "Email: admin@demo.com" -ForegroundColor White
    Write-Host "Senha: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "O sistema esta pronto para uso!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "SISTEMA INICIADO COM $errosEncontrados PROBLEMA(S)" -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verifique os erros acima e tente novamente." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Comandos uteis para diagnostico:" -ForegroundColor Gray
    Write-Host "1. Execute: .\verificar_status.ps1" -ForegroundColor White
    Write-Host "2. Consulte: MANUAL_USUARIO_FINAL.md" -ForegroundColor White
    Write-Host "3. Em caso de problemas: .\reiniciar_sistema_completo.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "Para mais informacoes, consulte: MANUAL_USUARIO_FINAL.md" -ForegroundColor Gray
Write-Host "Para diagnostico rapido, execute: .\verificar_status.ps1" -ForegroundColor Gray

pause
