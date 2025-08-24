# Iniciar Sistema Completo - Sistema de Auditoria Fiscal
# Script para iniciar todos os componentes do sistema de uma só vez

Write-Host "🚀 INICIANDO SISTEMA COMPLETO DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

$inicioExecucao = Get-Date
$errosEncontrados = 0

# Verificar se estamos na pasta correta
if (-not (Test-Path "config.py")) {
    Write-Host "❌ ERRO: Execute este script na pasta raiz do projeto!" -ForegroundColor Red
    Write-Host "📂 Pasta atual: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "📂 Pasta esperada: contendo config.py" -ForegroundColor Yellow
    pause
    exit 1
}

# Função para verificar se uma porta está em uso
function Test-Port {
    param($porta)
    $conexao = netstat -an | findstr ":$porta "
    return $conexao -ne $null
}

# Função para aguardar serviço ficar disponível
function Wait-ForService {
    param($porta, $nomeServico, $tempoLimite = 60)
    
    Write-Host "⏳ Aguardando $nomeServico ficar disponível..." -ForegroundColor Yellow
    $tempoInicio = Get-Date
    
    do {
        Start-Sleep -Seconds 2
        $disponivel = Test-Port $porta
        $tempoDecorrido = (Get-Date) - $tempoInicio
        
        if ($tempoDecorrido.TotalSeconds -gt $tempoLimite) {
            Write-Host "⚠️ Timeout aguardando $nomeServico" -ForegroundColor Yellow
            return $false
        }
    } while (-not $disponivel)
    
    Write-Host "✅ $nomeServico disponível!" -ForegroundColor Green
    return $true
}

Write-Host "🔍 1. VERIFICAÇÃO INICIAL..." -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Verificar Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker não encontrado!" -ForegroundColor Red
    Write-Host "💡 Instale o Docker Desktop e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

# Verificar Conda
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Anaconda/Conda não encontrado!" -ForegroundColor Red
    Write-Host "💡 Instale o Anaconda e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

# Verificar Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js não encontrado!" -ForegroundColor Red
    Write-Host "💡 Instale o Node.js e tente novamente" -ForegroundColor Yellow
    $errosEncontrados++
}

if ($errosEncontrados -gt 0) {
    Write-Host ""
    Write-Host "❌ $errosEncontrados erro(s) encontrado(s)!" -ForegroundColor Red
    Write-Host "💡 Corrija os problemas acima antes de continuar" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Todas as dependências encontradas!" -ForegroundColor Green
Write-Host ""

Write-Host "🐳 2. INICIANDO SERVIÇOS BASE..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Verificar se Docker está rodando
try {
    docker version | Out-Null
    Write-Host "✅ Docker está funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host "💡 Inicie o Docker Desktop e tente novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Iniciar PostgreSQL se não estiver rodando
if (-not (Test-Port 5432)) {
    Write-Host "🔄 Iniciando PostgreSQL..." -ForegroundColor Yellow
    
    # Verificar se container existe
    $pgContainer = docker ps -a --filter "name=auditoria_postgres" --format "{{.Names}}"
    if ($pgContainer) {
        Write-Host "📦 Container PostgreSQL encontrado, iniciando..." -ForegroundColor White
        docker start auditoria_postgres | Out-Null
    } else {
        Write-Host "📦 Criando container PostgreSQL..." -ForegroundColor White
        docker run -d --name auditoria_postgres -e POSTGRES_DB=auditoria_fiscal -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin123 -p 5432:5432 postgres:13
    }
    
    if (Wait-ForService 5432 "PostgreSQL" 30) {
        Write-Host "✅ PostgreSQL iniciado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Falha ao iniciar PostgreSQL" -ForegroundColor Red
        $errosEncontrados++
    }
} else {
    Write-Host "✅ PostgreSQL já está rodando" -ForegroundColor Green
}

# Iniciar Redis se não estiver rodando
if (-not (Test-Port 6379)) {
    Write-Host "🔄 Iniciando Redis..." -ForegroundColor Yellow
    
    # Verificar se container existe
    $redisContainer = docker ps -a --filter "name=auditoria_redis" --format "{{.Names}}"
    if ($redisContainer) {
        Write-Host "📦 Container Redis encontrado, iniciando..." -ForegroundColor White
        docker start auditoria_redis | Out-Null
    } else {
        Write-Host "📦 Criando container Redis..." -ForegroundColor White
        docker run -d --name auditoria_redis -p 6379:6379 redis:7-alpine
    }
    
    if (Wait-ForService 6379 "Redis" 20) {
        Write-Host "✅ Redis iniciado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Falha ao iniciar Redis" -ForegroundColor Red
        $errosEncontrados++
    }
} else {
    Write-Host "✅ Redis já está rodando" -ForegroundColor Green
}

# Iniciar Ollama se não estiver rodando
if (-not (Test-Port 11434)) {
    Write-Host "🔄 Iniciando Ollama..." -ForegroundColor Yellow
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        
        if (Wait-ForService 11434 "Ollama" 30) {
            Write-Host "✅ Ollama iniciado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "❌ Falha ao iniciar Ollama" -ForegroundColor Red
            $errosEncontrados++
        }
    } else {
        Write-Host "⚠️ Ollama não encontrado, pulando..." -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Ollama já está rodando" -ForegroundColor Green
}

Write-Host ""

Write-Host "🐍 3. INICIANDO BACKEND..." -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Verificar se ambiente conda existe
$condaEnvs = conda env list | findstr auditoria-fiscal
if (-not $condaEnvs) {
    Write-Host "❌ Ambiente conda 'auditoria-fiscal' não encontrado!" -ForegroundColor Red
    Write-Host "💡 Execute: conda env create -f environment.yml" -ForegroundColor Yellow
    $errosEncontrados++
} else {
    Write-Host "✅ Ambiente conda encontrado" -ForegroundColor Green
    
    # Verificar se backend já está rodando
    if (Test-Port 8000) {
        Write-Host "✅ Backend já está rodando na porta 8000" -ForegroundColor Green
    } else {
        Write-Host "🔄 Iniciando backend..." -ForegroundColor Yellow
        
        # Criar script temporário para iniciar backend
        $scriptBackend = @'
conda activate auditoria-fiscal
cd microservices\gateway
Write-Host "🚀 Iniciando Gateway..." -ForegroundColor Green
python main.py
'@
        
        $scriptBackend | Out-File -FilePath "temp_start_backend.ps1" -Encoding UTF8
        
        # Executar em nova janela
        Start-Process powershell.exe -ArgumentList "-NoExit", "-File", "temp_start_backend.ps1" -WindowStyle Normal
        
        # Aguardar backend ficar disponível
        if (Wait-ForService 8000 "Backend" 60) {
            Write-Host "✅ Backend iniciado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "❌ Falha ao iniciar Backend" -ForegroundColor Red
            $errosEncontrados++
        }
        
        # Remover script temporário
        Start-Sleep -Seconds 2
        Remove-Item "temp_start_backend.ps1" -ErrorAction SilentlyContinue
    }
}

Write-Host ""

Write-Host "🌐 4. INICIANDO FRONTEND..." -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

if (Test-Path "frontend") {
    # Verificar se frontend já está rodando
    if (Test-Port 3001) {
        Write-Host "✅ Frontend já está rodando na porta 3001" -ForegroundColor Green
    } else {
        Write-Host "🔄 Iniciando frontend..." -ForegroundColor Yellow
        
        # Verificar se node_modules existe
        if (-not (Test-Path "frontend\node_modules")) {
            Write-Host "📦 Instalando dependências do frontend..." -ForegroundColor White
            cd frontend
            npm install
            cd ..
        }
        
        # Criar script temporário para iniciar frontend
        $scriptFrontend = @'
cd frontend
if (-not (Test-Path ".env.local")) {
    Write-Host "📝 Criando arquivo .env.local..." -ForegroundColor Yellow
    "REACT_APP_API_URL=http://localhost:8000" | Out-File -FilePath ".env.local" -Encoding UTF8
    "REACT_APP_ENVIRONMENT=local" | Add-Content -Path ".env.local" -Encoding UTF8
}
Write-Host "🚀 Iniciando servidor React..." -ForegroundColor Green
npm start
'@
        
        $scriptFrontend | Out-File -FilePath "temp_start_frontend.ps1" -Encoding UTF8
        
        # Executar em nova janela
        Start-Process powershell.exe -ArgumentList "-NoExit", "-File", "temp_start_frontend.ps1" -WindowStyle Normal
        
        # Aguardar frontend ficar disponível
        if (Wait-ForService 3001 "Frontend" 90) {
            Write-Host "✅ Frontend iniciado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "❌ Falha ao iniciar Frontend" -ForegroundColor Red
            $errosEncontrados++
        }
        
        # Remover script temporário
        Start-Sleep -Seconds 2
        Remove-Item "temp_start_frontend.ps1" -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "⚠️ Pasta frontend não encontrada" -ForegroundColor Yellow
    $errosEncontrados++
}

Write-Host ""

# Status final
$tempoExecucao = (Get-Date) - $inicioExecucao
$tempoFormatado = "{0:mm}:{0:ss}" -f $tempoExecucao

Write-Host "🎉 INICIALIZAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""
Write-Host "⏱️ Tempo total: $tempoFormatado" -ForegroundColor White
Write-Host "❌ Erros encontrados: $errosEncontrados" -ForegroundColor White
Write-Host ""

if ($errosEncontrados -eq 0) {
    Write-Host "✅ SISTEMA TOTALMENTE OPERACIONAL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 ACESSOS DISPONÍVEIS:" -ForegroundColor Cyan
    Write-Host "• Frontend: http://localhost:3001" -ForegroundColor White
    Write-Host "• Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "• Documentação: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "• Health Check: http://localhost:8000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "👤 LOGIN PADRÃO:" -ForegroundColor Cyan
    Write-Host "• Email: admin@demo.com" -ForegroundColor White
    Write-Host "• Senha: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 DICA: O navegador abrirá automaticamente em alguns segundos" -ForegroundColor Yellow
    
    # Aguardar um pouco e abrir navegador
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:3001"
    
} else {
    Write-Host "⚠️ SISTEMA INICIADO COM $errosEncontrados PROBLEMA(S)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔧 SOLUÇÕES RECOMENDADAS:" -ForegroundColor Cyan
    Write-Host "1. Execute: .\verificar_status.ps1" -ForegroundColor White
    Write-Host "2. Consulte: MANUAL_USUARIO_FINAL.md" -ForegroundColor White
    Write-Host "3. Em caso de problemas: .\reiniciar_sistema_completo.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "📖 Para mais informações, consulte: MANUAL_USUARIO_FINAL.md" -ForegroundColor Gray
Write-Host "🔧 Para diagnóstico rápido, execute: .\verificar_status.ps1" -ForegroundColor Gray

pause
