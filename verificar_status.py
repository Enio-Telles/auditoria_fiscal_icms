#!/usr/bin/env python3
"""
🔍 VERIFICADOR DE STATUS DO SISTEMA
===================================
Verifica se todos os componentes estão prontos para execução do plano completo
"""

import os
import sys
import requests
import subprocess
from datetime import datetime
from pathlib import Path


class StatusVerifier:
    def __init__(self):
        self.checks_passed = 0
        self.total_checks = 0
        self.issues = []

    def check(self, name, func):
        """Executar uma verificação"""
        self.total_checks += 1
        print(f"🔍 Verificando: {name}...", end=" ")

        try:
            result = func()
            if result:
                print("✅")
                self.checks_passed += 1
                return True
            else:
                print("❌")
                self.issues.append(f"❌ {name}")
                return False
        except Exception as e:
            print(f"❌ (Erro: {e})")
            self.issues.append(f"❌ {name}: {e}")
            return False

    def verify_conda_environment(self):
        """Verificar ambiente Conda"""
        env_name = os.environ.get("CONDA_DEFAULT_ENV", "")
        return "auditoria" in env_name.lower()

    def verify_python_version(self):
        """Verificar versão do Python"""
        return sys.version_info >= (3, 11)

    def verify_required_packages(self):
        """Verificar pacotes Python necessários"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "psycopg2-binary",
            "pandas",
            "numpy",
            "requests",
            "pydantic",
            "pathlib",
            "sentence-transformers",
            "chromadb",
            "ollama",
        ]

        try:
            import pkg_resources

            installed = [pkg.project_name.lower() for pkg in pkg_resources.working_set]

            missing = []
            for package in required_packages:
                # Verificar variações do nome
                package_variants = [
                    package,
                    package.replace("-", "_"),
                    package.replace("_", "-"),
                ]

                if not any(variant in installed for variant in package_variants):
                    missing.append(package)

            if missing:
                self.issues.append(f"Pacotes faltando: {', '.join(missing)}")
                return False

            return True
        except Exception:
            return False

    def verify_nodejs(self):
        """Verificar Node.js"""
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def verify_microservices(self):
        """Verificar se microserviços estão online"""

        services = {
            "Gateway": "http://localhost:8000/health",
            "Auth": "http://localhost:8001/health",
            "Tenant": "http://localhost:8002/health",
            "Product": "http://localhost:8003/health",
            "Classification": "http://localhost:8004/health",
            "Import": "http://localhost:8005/health",
            "AI": "http://localhost:8006/health",
        }

        online_services = 0
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    online_services += 1
            except Exception:
                continue

        # Pelo menos 5 dos 7 serviços devem estar online
        return online_services >= 5

    def verify_ollama(self):
        """Verificar Ollama e modelos"""
        try:
            # Verificar se Ollama está rodando
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                return False

            # Verificar modelos instalados
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            # Verificar se pelo menos um modelo está disponível
            required_models = ["phi3:mini", "llama3", "mistral"]
            has_model = any(model in str(model_names) for model in required_models)

            return has_model
        except Exception:
            return False

    def verify_database(self):
        """Verificar conexão com banco de dados"""
        try:
            # Tentar conectar via microserviço
            response = requests.get("http://localhost:8002/tenants", timeout=5)
            return response.status_code in [200, 401]  # 401 é OK (sem auth)
        except Exception:
            return False

    def verify_base_data_files(self):
        """Verificar arquivos de dados base"""

        required_files = [
            "data/raw/01_Tabela_NCM.xlsx",
            "data/raw/02_conv_142_formatado.json",
            "data/raw/Tabela_NESH_CEST_2022.xlsx",
        ]

        existing_files = 0
        for file_path in required_files:
            if os.path.exists(file_path):
                existing_files += 1

        # Pelo menos 2 dos 3 arquivos devem existir
        return existing_files >= 2

    def verify_frontend_build(self):
        """Verificar se frontend está compilado"""
        build_dir = Path("frontend/build")
        node_modules = Path("frontend/node_modules")

        return build_dir.exists() or node_modules.exists()

    def verify_scripts_ready(self):
        """Verificar se scripts estão prontos"""

        required_scripts = [
            "scripts/fase1_implementacao.py",
            "executar_plano_completo.py",
        ]

        return all(os.path.exists(script) for script in required_scripts)

    def verify_disk_space(self):
        """Verificar espaço em disco"""
        try:
            import shutil

            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            return free_gb >= 2  # Pelo menos 2GB livres
        except Exception:
            return False

    def verify_network_access(self):
        """Verificar acesso à rede"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def run_all_checks(self):
        """Executar todas as verificações"""

        print("🔍 VERIFICAÇÃO DE STATUS DO SISTEMA")
        print("=" * 50)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()

        # Lista de verificações
        checks = [
            ("Ambiente Conda", self.verify_conda_environment),
            ("Python 3.11+", self.verify_python_version),
            ("Pacotes Python", self.verify_required_packages),
            ("Node.js", self.verify_nodejs),
            ("Microserviços", self.verify_microservices),
            ("Ollama + Modelos", self.verify_ollama),
            ("Banco de Dados", self.verify_database),
            ("Arquivos de Dados", self.verify_base_data_files),
            ("Frontend", self.verify_frontend_build),
            ("Scripts", self.verify_scripts_ready),
            ("Espaço em Disco", self.verify_disk_space),
            ("Acesso à Rede", self.verify_network_access),
        ]

        # Executar verificações
        for check_name, check_func in checks:
            self.check(check_name, check_func)

        # Resumo
        print("\n" + "=" * 50)
        print("📊 RESUMO DA VERIFICAÇÃO")
        print("=" * 50)

        success_rate = (self.checks_passed / self.total_checks) * 100
        print(
            f"✅ Verificações passaram: {self.checks_passed}/{self.total_checks} ({success_rate:.1f}%)"
        )

        if self.issues:
            print(f"\n❌ PROBLEMAS ENCONTRADOS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")

        # Determinar status geral
        if success_rate >= 90:
            status = "🟢 EXCELENTE"
            recommendation = "Sistema pronto para execução do plano completo!"
        elif success_rate >= 75:
            status = "🟡 BOM"
            recommendation = (
                "Sistema funcional, mas recomenda-se resolver problemas menores."
            )
        elif success_rate >= 60:
            status = "🟠 REGULAR"
            recommendation = "Resolver problemas críticos antes de continuar."
        else:
            status = "🔴 CRÍTICO"
            recommendation = (
                "Sistema não está pronto. Resolver todos os problemas primeiro."
            )

        print(f"\n📋 STATUS GERAL: {status}")
        print(f"💡 RECOMENDAÇÃO: {recommendation}")

        # Próximos passos
        if success_rate >= 75:
            print("\n🚀 PRÓXIMOS PASSOS:")
            print("1. Execute: python executar_plano_completo.py")
            print("2. Acompanhe o progresso das 4 fases")
            print("3. Teste o sistema final")
        else:
            print("\n🔧 AÇÕES NECESSÁRIAS:")
            if "Microserviços" in str(self.issues):
                print("1. Execute: start_microservices.bat")
            if "Ollama" in str(self.issues):
                print("2. Inicie o Ollama e instale modelos")
            if "Pacotes Python" in str(self.issues):
                print("3. Execute: pip install -r requirements.txt")
            if "Node.js" in str(self.issues):
                print("4. Instale Node.js e configure frontend")

        return success_rate >= 75


def main():
    verifier = StatusVerifier()
    system_ready = verifier.run_all_checks()

    if system_ready:
        print("\n✅ Sistema pronto para execução!")
        return 0
    else:
        print("\n❌ Sistema não está pronto!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
