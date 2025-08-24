# 🚀 GUIA PASSO A PASSO - DOCKER NO WINDOWS 11
# Sistema de Auditoria Fiscal ICMS v4.0

Write-Host "GUIA PASSO A PASSO - DOCKER WINDOWS 11" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

Write-Host "PASSO 1: VERIFICAR DOCKER DESKTOP" -ForegroundColor Cyan
Write-Host "---------------------------------"
Write-Host "1.1. Procure o icone do Docker na bandeja do sistema (canto inferior direito)" -ForegroundColor White
Write-Host "1.2. Se nao houver icone, Docker nao esta rodando" -ForegroundColor White
Write-Host "1.3. Se o icone estiver 'piscando' ou animando, Docker esta inicializando" -ForegroundColor White
Write-Host ""

Write-Host "PASSO 2: INICIAR DOCKER DESKTOP" -ForegroundColor Cyan
Write-Host "-------------------------------"
Write-Host "2.1. Menu Iniciar > Digite 'Docker Desktop' > Enter" -ForegroundColor White
Write-Host "2.2. OU clique duas vezes no atalho da area de trabalho" -ForegroundColor White
Write-Host "2.3. OU execute: Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" -ForegroundColor White
Write-Host ""

Write-Host "PASSO 3: AGUARDAR INICIALIZACAO" -ForegroundColor Cyan
Write-Host "-------------------------------"
Write-Host "3.1. Aguarde 1-2 minutos" -ForegroundColor White
Write-Host "3.2. Observe o icone na bandeja parar de piscar" -ForegroundColor White
Write-Host "3.3. Clique no icone para ver status 'Docker Desktop is running'" -ForegroundColor White
Write-Host ""

Write-Host "PASSO 4: TESTAR DOCKER" -ForegroundColor Cyan
Write-Host "---------------------"
Write-Host "4.1. Abra PowerShell (pode ser este mesmo)" -ForegroundColor White
Write-Host "4.2. Execute: docker --version" -ForegroundColor White
Write-Host "4.3. Deve retornar algo como: 'Docker version 24.x.x'" -ForegroundColor White
Write-Host "4.4. Execute: docker info" -ForegroundColor White
Write-Host "4.5. Deve mostrar informacoes do Docker sem erros" -ForegroundColor White
Write-Host ""

Write-Host "PASSO 5: CRIAR AMBIENTE LOCAL" -ForegroundColor Cyan
Write-Host "-----------------------------"
Write-Host "5.1. Execute: docker network create auditoria-local-network" -ForegroundColor White
Write-Host "5.2. Execute: .\scripts\iniciar_docker_simples.ps1" -ForegroundColor White
Write-Host "5.3. OU execute: .\start_sistema_local.ps1" -ForegroundColor White
Write-Host ""

Write-Host "PROBLEMAS COMUNS:" -ForegroundColor Yellow
Write-Host "=================" -ForegroundColor Yellow
Write-Host ""

Write-Host "PROBLEMA: Docker nao inicia" -ForegroundColor Red
Write-Host "SOLUCAO:" -ForegroundColor Green
Write-Host "- Reinicie o computador" -ForegroundColor White
Write-Host "- Execute como Administrador" -ForegroundColor White
Write-Host "- Verifique se WSL2 esta habilitado: wsl --install" -ForegroundColor White
Write-Host ""

Write-Host "PROBLEMA: 'The system cannot find the file specified'" -ForegroundColor Red
Write-Host "SOLUCAO:" -ForegroundColor Green
Write-Host "- Docker Desktop nao esta rodando completamente" -ForegroundColor White
Write-Host "- Aguarde mais tempo (ate 3 minutos)" -ForegroundColor White
Write-Host "- Reinicie Docker Desktop" -ForegroundColor White
Write-Host ""

Write-Host "PROBLEMA: 'Access denied' ou permissoes" -ForegroundColor Red
Write-Host "SOLUCAO:" -ForegroundColor Green
Write-Host "- Execute PowerShell como Administrador" -ForegroundColor White
Write-Host "- Adicione seu usuario ao grupo 'docker-users'" -ForegroundColor White
Write-Host "- Reinicie o computador apos adicionar ao grupo" -ForegroundColor White
Write-Host ""

Write-Host "VERIFICACAO FINAL:" -ForegroundColor Magenta
Write-Host "=================" -ForegroundColor Magenta
Write-Host "Quando tudo estiver funcionando, voce vera:" -ForegroundColor White
Write-Host "- docker --version retorna versao sem erros" -ForegroundColor Green
Write-Host "- docker ps retorna tabela vazia sem erros" -ForegroundColor Green
Write-Host "- docker network ls mostra redes disponivel" -ForegroundColor Green
Write-Host ""

Write-Host "PROXIMOS PASSOS APOS DOCKER FUNCIONANDO:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Execute: .\start_sistema_local.ps1" -ForegroundColor White
Write-Host "2. Aguarde containers iniciarem" -ForegroundColor White
Write-Host "3. Acesse: http://localhost:3000 (Frontend)" -ForegroundColor White
Write-Host "4. Acesse: http://localhost:8000/docs (API)" -ForegroundColor White
Write-Host ""

Write-Host "COMANDOS UTEIS:" -ForegroundColor Yellow
Write-Host "===============" -ForegroundColor Yellow
Write-Host "Ver containers rodando: docker ps" -ForegroundColor White
Write-Host "Ver todos containers: docker ps -a" -ForegroundColor White
Write-Host "Parar container: docker stop <nome>" -ForegroundColor White
Write-Host "Iniciar container: docker start <nome>" -ForegroundColor White
Write-Host "Ver logs: docker logs <nome>" -ForegroundColor White
Write-Host "Remover container: docker rm <nome>" -ForegroundColor White
Write-Host ""

Write-Host "AGORA EXECUTE:" -ForegroundColor Green
Write-Host "docker --version" -ForegroundColor White
