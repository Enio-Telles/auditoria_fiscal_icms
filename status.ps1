Write-Host "VERIFICACAO COMPLETA DO SISTEMA" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

Write-Host "1. Docker:"
docker --version

Write-Host "2. Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}"

Write-Host "3. PostgreSQL:"
docker exec auditoria_postgres pg_isready -U auditoria_user

Write-Host "4. Redis:"
docker exec auditoria_redis redis-cli ping

Write-Host ""
Write-Host "SISTEMA RODANDO EM:" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001"
Write-Host "Backend:  http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"
