@echo off
echo 🚀 Installing Frontend Dependencies...
echo Current directory: %CD%

cd frontend
echo Changed to: %CD%

echo Cleaning up previous installations...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

echo Installing dependencies...
npm cache clean --force
npm install --legacy-peer-deps --no-audit --no-fund

if %ERRORLEVEL% neq 0 (
    echo ❌ Installation failed, trying alternative approach...
    npm install --force
)

if %ERRORLEVEL% neq 0 (
    echo ❌ Installation failed, trying with yarn...
    npm install -g yarn
    yarn install
)

echo ✅ Installation completed!
echo To start the frontend: npm start
pause
