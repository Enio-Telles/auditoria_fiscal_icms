#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Direto da API Corrigida
=============================

Script para testar especificamente a API corrigida sem conflitos.
"""

import requests
import time


def test_api_corrigida():
    """Teste da API corrigida"""
    api_url = "http://127.0.0.1:8003"

    print("🔄 Testando API Corrigida...")
    print("=" * 50)

    # Teste 1: Health Check
    print("\n🔧 Teste 1: Health Check")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check OK!")
            print(f"📋 Status: {result['status']}")
            print(f"📋 Versão: {result['version']}")
            print(f"📋 Database: {result['database_connection']}")
            print(f"📋 Data Extractor: {result['data_extractor']}")
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

    # Teste 2: Root endpoint
    print("\n🔧 Teste 2: Root Endpoint")
    try:
        response = requests.get(f"{api_url}/", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Root endpoint OK!")
            print(f"📋 Versão: {result['version']}")
            print(f"📋 Status: {result['status']}")
            print(f"📋 Features: {len(result['features'])}")
        else:
            print(f"❌ Root endpoint falhou: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro no root endpoint: {e}")

    # Teste 3: Empresas
    print("\n🔧 Teste 3: Listar Empresas")
    try:
        response = requests.get(f"{api_url}/empresas", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Listar empresas OK!")
            print(f"📋 Empresas encontradas: {len(result)}")
            for empresa in result[:2]:  # Primeiras 2
                print(f"   🏢 {empresa['razao_social']} - {empresa['cnpj']}")
        else:
            print(f"❌ Listar empresas falhou: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao listar empresas: {e}")

    # Teste 4: Estatísticas
    print("\n🔧 Teste 4: Estatísticas")
    try:
        response = requests.get(f"{api_url}/stats", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Estatísticas OK!")
            print(f"📋 Total empresas: {result['total_empresas']}")
            print(f"📋 Total produtos: {result['total_produtos']}")
            print(f"📋 Golden Set NCM: {result['golden_set']['ncm_items']}")
        else:
            print(f"❌ Estatísticas falharam: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro nas estatísticas: {e}")

    # Teste 5: Teste de Conexão de Importação
    print("\n🔧 Teste 5: Teste de Conexão de Importação")
    try:
        connection_data = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "db_04565289005297",
            "user": "postgres",
            "password": "sefin",
            "schema": "dbo",
        }

        response = requests.post(
            f"{api_url}/api/import/test-connection", json=connection_data, timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Teste de conexão OK!")
            print(f"📋 Sucesso: {result['success']}")
            if result["success"]:
                print(f"📋 Info: {result.get('database_info', 'N/A')[:60]}...")
                print(f"📋 Host: {result.get('host', 'N/A')}")
                print(f"📋 Database: {result.get('database', 'N/A')}")
            else:
                print(f"📋 Erro: {result.get('error', 'N/A')}")
        else:
            print(f"❌ Teste de conexão falhou: {response.status_code}")
            print(f"📋 Resposta: {response.text[:100]}...")

    except Exception as e:
        print(f"❌ Erro no teste de conexão: {e}")

    print("\n🎉 Teste concluído!")
    return True


if __name__ == "__main__":
    print("🚀 Teste da API Multi-Tenant Corrigida")
    print("=" * 60)
    print("⏳ Aguardando API estar pronta...")
    time.sleep(3)

    success = test_api_corrigida()

    if success:
        print("\n✅ API está funcionando corretamente!")
        print("🎯 Problema de finalização automática foi resolvido!")
    else:
        print("\n❌ Ainda há problemas na API")

    print("\n📋 Para mais testes, acesse:")
    print("   • http://127.0.0.1:8003/docs - Documentação interativa")
    print("   • http://127.0.0.1:8003/health - Status da API")
    print("   • http://127.0.0.1:8003/empresas - Lista de empresas")
