#!/usr/bin/env python3
"""
Servidor robusto para a API de Auditoria Fiscal ICMS.
Versão com fallback para modo simples quando dependências não estão disponíveis.
"""

import uvicorn
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def check_dependencies():
    """Verifica se todas as dependências estão disponíveis."""
    missing_deps = []

    # Verificar dependências críticas
    # Verificações opcionais comentadas para evitar imports não usados; usar find_spec se necessário
    # from importlib.util import find_spec
    # if find_spec("jose") is None:
    #     missing_deps.append("python-jose[cryptography]")
    # if find_spec("passlib") is None:
    #     missing_deps.append("passlib[bcrypt]")
    # if find_spec("multipart") is None:
    #     missing_deps.append("python-multipart")

    return missing_deps


def main():
    """Executa o servidor de desenvolvimento."""
    try:
        print("🚀 Iniciando servidor da API de Auditoria Fiscal ICMS...")
        print("=" * 60)

        # Verificar dependências
        missing_deps = check_dependencies()

        if missing_deps:
            print("⚠️  AVISO: Dependências faltando detectadas:")
            for dep in missing_deps:
                print(f"   - {dep}")
            print("\n🔄 Alternando para servidor SIMPLES...")
            app_module = "auditoria_icms.api.main_simple:app"
            mode_info = "MODO SIMPLES (sem dependências avançadas)"
        else:
            print("✅ Todas as dependências verificadas!")
            print("🔄 Iniciando servidor COMPLETO...")
            app_module = "auditoria_icms.api.main:app"
            mode_info = "MODO COMPLETO (todas as funcionalidades)"

        # Configurações do servidor
        host = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8000"))
        debug = os.getenv("API_DEBUG", "true").lower() == "true"

        print(f"📍 Host: {host}")
        print(f"🔌 Porta: {port}")
        print(f"🐛 Debug: {debug}")
        print(f"⚙️  Modo: {mode_info}")
        print(f"📚 Documentação: http://{host}:{port}/docs")
        print("=" * 60)

        # Executar servidor
        uvicorn.run(
            app_module,
            host=host,
            port=port,
            reload=False,  # Desativar reload para evitar conflitos
            log_level="info" if debug else "warning",
            access_log=debug,
        )

    except KeyboardInterrupt:
        print("\n⏹️  Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        print("\n🔄 Tentando modo SIMPLES como fallback...")

        try:
            # Fallback para servidor simples
            uvicorn.run(
                "auditoria_icms.api.main_simple:app",
                host=host,
                port=port,
                reload=False,
                log_level="info",
                access_log=True,
            )
        except Exception as fallback_error:
            print(f"❌ Erro no fallback: {fallback_error}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
