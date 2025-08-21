#!/usr/bin/env python3
"""
Servidor com ativação automática do ambiente conda.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_with_conda():
    """Executa o servidor com o ambiente conda ativado."""
    
    print("🚀 Iniciando servidor da API de Auditoria Fiscal ICMS...")
    print("🔧 Ativando ambiente conda: auditoria-fiscal")
    print("=" * 60)
    
    # Configurações do servidor
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    
    # Script PowerShell para ativar conda e rodar servidor
    ps_script = f"""
    & C:\\ProgramData\\Anaconda3\\shell\\condabin\\conda-hook.ps1
    conda activate auditoria-fiscal
    
    # Verificar se as dependências estão disponíveis
    $depsOk = $true
    try {{
        python -c "import jose, passlib, multipart; print('✅ Todas as dependências OK')"
    }} catch {{
        $depsOk = $false
        Write-Host "⚠️  Algumas dependências faltando, usando modo simples"
    }}
    
    # Escolher o servidor baseado nas dependências
    if ($depsOk) {{
        Write-Host "🔄 Iniciando servidor COMPLETO..."
        Write-Host "📚 Documentação: http://{host}:{port}/docs"
        python run_server.py
    }} else {{
        Write-Host "🔄 Iniciando servidor SIMPLES..."
        Write-Host "📚 Documentação: http://{host}:{port}/docs"
        python run_simple_server.py
    }}
    """
    
    try:
        # Executar o script PowerShell
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            cwd=Path(__file__).parent,
            text=True,
            shell=True
        )
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\\n⏹️  Servidor interrompido pelo usuário")
        return 0
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_with_conda())
