#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup do Sistema de IA Local com Ollama
======================================

Script para configurar e instalar Ollama com modelos LLM locais
"""

import subprocess
import requests
import time
import platform
from pathlib import Path


def check_ollama_installed():
    """Verifica se Ollama está instalado"""
    try:
        result = subprocess.run(
            ["ollama", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def check_ollama_running():
    """Verifica se Ollama está rodando"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def start_ollama():
    """Inicia o serviço Ollama"""
    try:
        if platform.system() == "Windows":
            # No Windows, Ollama roda como serviço
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # Linux/Mac
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Aguardar inicialização
        for i in range(30):  # 30 segundos máximo
            if check_ollama_running():
                return True
            time.sleep(1)

        return False
    except Exception as e:
        print(f"❌ Erro ao iniciar Ollama: {e}")
        return False


def install_model(model_name: str, timeout: int = 600):
    """Instala um modelo específico"""
    print(f"📦 Baixando modelo {model_name}...")
    print("   (Isso pode demorar alguns minutos na primeira vez)")

    try:
        # Usar ollama pull diretamente
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Aguardar conclusão com timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                print(f"✅ Modelo {model_name} instalado com sucesso!")
                return True
            else:
                print(f"❌ Erro ao instalar {model_name}: {stderr}")
                return False
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"⏰ Timeout ao instalar {model_name}")
            return False

    except Exception as e:
        print(f"❌ Erro ao instalar modelo {model_name}: {e}")
        return False


def setup_ollama_system():
    """Configura sistema completo do Ollama"""
    print("🤖 SETUP DO SISTEMA DE IA LOCAL COM OLLAMA")
    print("=" * 60)

    # 1. Verificar se Ollama está instalado
    print("\n1️⃣ Verificando instalação do Ollama...")
    if not check_ollama_installed():
        print("❌ Ollama não encontrado!")
        print("\n📥 INSTRUÇÕES DE INSTALAÇÃO:")
        print("=" * 40)

        if platform.system() == "Windows":
            print("Windows:")
            print("1. Baixe o instalador: https://ollama.ai/download/windows")
            print("2. Execute o instalador e siga as instruções")
            print("3. Reinicie o terminal e execute este script novamente")
        else:
            print("Linux/Mac:")
            print("curl -fsSL https://ollama.ai/install.sh | sh")

        return False

    print("✅ Ollama instalado!")

    # 2. Verificar se está rodando
    print("\n2️⃣ Verificando se Ollama está rodando...")
    if not check_ollama_running():
        print("⚠️ Ollama não está rodando, tentando iniciar...")
        if start_ollama():
            print("✅ Ollama iniciado com sucesso!")
        else:
            print("❌ Falha ao iniciar Ollama")
            print("💡 Tente executar manualmente: ollama serve")
            return False
    else:
        print("✅ Ollama já está rodando!")

    # 3. Verificar modelos disponíveis
    print("\n3️⃣ Verificando modelos disponíveis...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get("models", [])
        model_names = [model["name"] for model in models]

        if model_names:
            print(f"📋 Modelos já instalados: {', '.join(model_names)}")
        else:
            print("📋 Nenhum modelo instalado ainda")

    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {e}")
        return False

    # 4. Instalar modelos recomendados
    print("\n4️⃣ Instalando modelos recomendados...")

    modelos_recomendados = [
        ("llama3.1:8b", "Modelo principal - mais preciso"),
        ("llama2:7b", "Modelo backup - mais rápido"),
    ]

    modelos_instalados = []

    for modelo, descricao in modelos_recomendados:
        # Verificar se já está instalado
        if any(modelo in name for name in model_names):
            print(f"✅ {modelo} já instalado - {descricao}")
            modelos_instalados.append(modelo)
            continue

        print(f"\n📦 Instalando {modelo} - {descricao}")
        if install_model(modelo):
            modelos_instalados.append(modelo)
        else:
            print(f"⚠️ Falha ao instalar {modelo}, continuando...")

    # 5. Teste básico
    print("\n5️⃣ Testando sistema...")
    if modelos_instalados:
        modelo_teste = modelos_instalados[0]
        print(f"🧪 Testando modelo {modelo_teste}...")

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": modelo_teste,
                    "prompt": "Responda apenas: OK",
                    "stream": False,
                    "options": {"num_predict": 10},
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                resposta = result.get("response", "").strip()
                print(f"✅ Teste bem-sucedido! Resposta: '{resposta}'")

                # Salvar configuração
                config_data = {
                    "ollama_status": "ready",
                    "modelos_instalados": modelos_instalados,
                    "modelo_principal": modelos_instalados[0],
                    "data_setup": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                config_file = Path("config/ollama_config.json")
                config_file.parent.mkdir(parents=True, exist_ok=True)

                import json

                with open(config_file, "w") as f:
                    json.dump(config_data, f, indent=2)

                print(f"📄 Configuração salva em: {config_file}")

            else:
                print(f"❌ Teste falhou: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            return False

    else:
        print("❌ Nenhum modelo foi instalado com sucesso")
        return False

    # 6. Resultado final
    print("\n🎉 SETUP CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print("✅ Ollama rodando em: http://localhost:11434")
    print(f"✅ Modelos disponíveis: {', '.join(modelos_instalados)}")
    print("✅ Sistema pronto para classificação de produtos!")
    print("\n💡 Para testar:")
    print("   python src/auditoria_icms/ai/local_llm_classifier.py --test")

    return True


def check_system_status():
    """Verifica status atual do sistema"""
    print("📊 STATUS DO SISTEMA DE IA LOCAL")
    print("=" * 40)

    # Ollama instalado?
    ollama_installed = check_ollama_installed()
    print(f"Ollama instalado: {'✅ SIM' if ollama_installed else '❌ NÃO'}")

    if not ollama_installed:
        print("❌ Execute o setup primeiro!")
        return

    # Ollama rodando?
    ollama_running = check_ollama_running()
    print(f"Ollama rodando: {'✅ SIM' if ollama_running else '❌ NÃO'}")

    if not ollama_running:
        print("💡 Execute: ollama serve")
        return

    # Modelos disponíveis
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print(f"Modelos instalados: ✅ {len(models)}")
                for model in models:
                    size_gb = model.get("size", 0) / (1024**3)
                    print(f"  • {model['name']} ({size_gb:.1f}GB)")
            else:
                print("Modelos instalados: ❌ NENHUM")
        else:
            print("❌ Erro ao conectar com Ollama")
    except Exception as e:
        print(f"❌ Erro: {e}")

    # Teste rápido
    print("\n🧪 Teste rápido...")
    try:
        from src.auditoria_icms.ai.local_llm_classifier import LocalLLMClassifier

        classifier = LocalLLMClassifier()

        if classifier.check_ollama_connection():
            print("✅ Conexão OK")

            # Teste de classificação
            result = classifier.classify_product("teste", "Notebook Dell")
            if result.ncm_sugerido != "0000.00.00":
                print(f"✅ Classificação OK: {result.ncm_sugerido}")
            else:
                print("⚠️ Classificação com problemas")
        else:
            print("❌ Falha na conexão")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup do Sistema de IA Local")
    parser.add_argument("--setup", action="store_true", help="Executar setup completo")
    parser.add_argument("--status", action="store_true", help="Verificar status")
    parser.add_argument("--start", action="store_true", help="Iniciar Ollama")

    args = parser.parse_args()

    if args.setup:
        setup_ollama_system()
    elif args.status:
        check_system_status()
    elif args.start:
        if start_ollama():
            print("✅ Ollama iniciado!")
        else:
            print("❌ Falha ao iniciar Ollama")
    else:
        print("🤖 Sistema de IA Local - Ollama")
        print("=" * 40)
        print("Opções:")
        print("  --setup   Configurar sistema completo")
        print("  --status  Verificar status atual")
        print("  --start   Iniciar serviço Ollama")
        print("\nExemplo: python setup_ollama.py --setup")
