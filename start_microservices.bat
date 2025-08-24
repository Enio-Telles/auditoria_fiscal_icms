@echo off
echo Starting Microservices Architecture for Auditoria Fiscal ICMS
echo ============================================================

cd microservices

echo.
echo Starting services with Docker Compose...
docker-compose up --build -d

echo.
echo Waiting for services to initialize...
timeout /t 30

echo.
echo Services Status:
docker-compose ps

echo.
echo API Gateway available at: http://localhost:8000
echo Authentication Service at: http://localhost:8001
echo Tenant Service at: http://localhost:8002
echo Product Service at: http://localhost:8003
echo Classification Service at: http://localhost:8004
echo Import Service at: http://localhost:8005
echo AI Service at: http://localhost:8006

echo.
echo Health check:
curl -s http://localhost:8000/health

echo.
echo Microservices are running!
echo Use 'docker-compose logs -f' to view logs
echo Use 'docker-compose down' to stop services

pause
