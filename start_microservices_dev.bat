@echo off
echo Starting Microservices in Development Mode (Conda Environment)
echo ==============================================================

call conda activate auditoria-fiscal-icms

if errorlevel 1 (
    echo Error: Could not activate conda environment 'auditoria-fiscal-icms'
    echo Please run setup_conda_environment.bat first
    pause
    exit /b 1
)

echo.
echo Environment activated successfully!
echo.

cd microservices

echo Starting PostgreSQL (if not running)...
echo Please ensure PostgreSQL is running on localhost:5432
echo Database: auditoria_fiscal_icms
echo User: postgres
echo Password: admin
echo.

echo Starting services...
echo.

echo Starting API Gateway on port 8000...
start "API Gateway" cmd /k "python gateway\main.py"
timeout /t 2

echo Starting Auth Service on port 8001...
start "Auth Service" cmd /k "python auth-service\main.py"
timeout /t 2

echo Starting Tenant Service on port 8002...
start "Tenant Service" cmd /k "python tenant-service\main.py"
timeout /t 2

echo Starting Product Service on port 8003...
start "Product Service" cmd /k "python product-service\main.py"
timeout /t 2

echo Starting Classification Service on port 8004...
start "Classification Service" cmd /k "python classification-service\main.py"
timeout /t 2

echo Starting Import Service on port 8005...
start "Import Service" cmd /k "python import-service\main.py"
timeout /t 2

echo Starting AI Service on port 8006...
start "AI Service" cmd /k "python ai-service\main.py"
timeout /t 2

echo.
echo All services are starting...
echo.
echo API Gateway: http://localhost:8000
echo Auth Service: http://localhost:8001
echo Tenant Service: http://localhost:8002
echo Product Service: http://localhost:8003
echo Classification Service: http://localhost:8004
echo Import Service: http://localhost:8005
echo AI Service: http://localhost:8006
echo.
echo Press any key to continue and check service status...
pause

echo.
echo Checking service health...
curl -s http://localhost:8000/health
echo.

echo.
echo Microservices are running in development mode!
echo Close the service windows to stop the services.

pause
