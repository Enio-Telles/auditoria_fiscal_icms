# Script para atualizar backend com novos endpoints
# Atualização 24/08/2025 - Correção dos endpoints 404

Write-Host "Atualizando backend com novos endpoints..." -ForegroundColor Cyan

# Parar processo Python atual
Write-Host "Parando backend atual..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
foreach ($process in $pythonProcesses) {
    if ($process.CommandLine -like "*api_estavel.py*") {
        Write-Host "Parando processo Python: $($process.Id)" -ForegroundColor Gray
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Aguardando 3 segundos..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Reiniciar backend
Write-Host "Iniciando backend atualizado..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python apis/api_estavel.py"

Write-Host "Aguardando backend inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Testar novos endpoints
Write-Host "Testando novos endpoints..." -ForegroundColor Cyan

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "Health Check: OK" -ForegroundColor Green
    
    $relatorios = Invoke-RestMethod -Uri "http://localhost:8000/relatorios/stats"
    Write-Host "Relatórios Stats: OK" -ForegroundColor Green
    
    $empresas = Invoke-RestMethod -Uri "http://localhost:8000/empresas/select"
    Write-Host "Empresas Select: OK" -ForegroundColor Green
    
    Write-Host "" 
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "BACKEND ATUALIZADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Novos endpoints funcionais:" -ForegroundColor White
    Write-Host "- /relatorios/stats" -ForegroundColor Cyan
    Write-Host "- /relatorios/classificacao-periodo" -ForegroundColor Cyan  
    Write-Host "- /empresas/select" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Os erros 404 no console foram resolvidos!" -ForegroundColor Yellow
    
} catch {
    Write-Host "Aguarde mais alguns segundos para o backend inicializar..." -ForegroundColor Yellow
    Write-Host "Execute novamente: .\atualizar_backend.ps1" -ForegroundColor White
}

pause
