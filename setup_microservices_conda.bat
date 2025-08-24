@echo off
echo Setting up Conda Environment for Microservices
echo ==============================================

echo.
echo Using existing main conda environment: auditoria-fiscal-icms
echo.

echo Activating environment...
call conda activate auditoria-fiscal-icms

if errorlevel 1 (
    echo Error: Main environment not found. Please run setup_conda_environment.bat first
    pause
    exit /b 1
)

echo.
echo Installing additional microservices dependencies...
pip install fastapi uvicorn httpx

echo.
echo Environment setup complete!
echo.
echo To activate the environment manually, run:
echo conda activate auditoria-fiscal-icms
echo.
echo To start the microservices, run:
echo start_microservices_dev.bat

pause
