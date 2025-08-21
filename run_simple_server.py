#!/usr/bin/env python3
"""
Servidor simples para a API de Auditoria Fiscal ICMS (sem dependências avançadas).
"""

import uvicorn
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Executa o servidor simples de desenvolvimento."""
    try:
        print("🚀 Iniciando servidor SIMPLES da API de Auditoria Fiscal ICMS...")
        print("=" * 60)
        
        # Configurações do servidor
        host = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8000"))
        debug = os.getenv("API_DEBUG", "true").lower() == "true"
        
        print(f"📍 Host: {host}")
        print(f"🔌 Porta: {port}")
        print(f"🐛 Debug: {debug}")
        print(f"📚 Documentação: http://{host}:{port}/docs")
        print("⚠️  Versão SIMPLES - sem workflows avançados")
        print("=" * 60)
        
        # Executar servidor simples
        uvicorn.run(
            "auditoria_icms.api.main_simple:app",
            host=host,
            port=port,
            reload=False,  # Disable reload to avoid conflicts
            log_level="info" if debug else "warning",
            access_log=debug
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
