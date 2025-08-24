#!/usr/bin/env python3
import requests


def test_frontend_import_correctly():
    """Testa importação com formato correto"""
    print("🎯 TESTE DE IMPORTAÇÃO - FORMATO CORRETO")
    print("=" * 50)

    # 1. Dados de conexão (no body)
    connection_data = {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "db_04565289005297",
        "user": "postgres",
        "password": "sefin",
        "schema": "dbo",
    }

    # 2. Query SQL (como parâmetro)
    sql_query = """
    SELECT
        produto_id,
        descricao_produto,
        codigo_produto,
        codigo_barra,
        ncm,
        cest,
        DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
        COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
    FROM dbo.produto
    WHERE descricao_produto IS NOT NULL
    """

    # 3. Parâmetros da query
    params = {"sql_query": sql_query, "limit": 100}

    print("📋 Configuração:")
    print(f"   Database: {connection_data['database']}")
    print(f"   Host: {connection_data['host']}")
    print(f"   Limit: {params['limit']}")

    try:
        print("\n🔄 Executando preview...")

        response = requests.post(
            "http://localhost:8000/api/import/preview",
            json=connection_data,
            params=params,
            headers={
                "Content-Type": "application/json",
                "Origin": "http://localhost:3001",
            },
            timeout=20,
        )

        print("\n📊 Resultado:")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ PREVIEW: SUCESSO!")
            print(f"   Sucesso: {result.get('success', False)}")
            print(f"   Registros: {result.get('preview_count', 0)}")
            print(f"   Colunas: {result.get('columns', [])}")

            # Mostrar alguns dados
            data = result.get("data", [])
            if data:
                print(f"\n📋 Primeiros {min(3, len(data))} registros:")
                for i, row in enumerate(data[:3]):
                    print(f"   {i+1}. {row}")

            return True
        else:
            print("❌ PREVIEW: ERRO")
            print(f"   Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def simulate_full_frontend_flow():
    """Simula o fluxo completo do frontend"""
    print("\n🌐 SIMULAÇÃO COMPLETA DO FRONTEND")
    print("=" * 45)

    connection_data = {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "db_04565289005297",
        "user": "postgres",
        "password": "sefin",
        "schema": "dbo",
    }

    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3001",
        "Accept": "application/json",
    }

    # Passo 1: Teste de conexão
    print("\n1️⃣ Testando conexão...")
    try:
        response = requests.post(
            "http://localhost:8000/api/import/test-connection",
            json=connection_data,
            headers=headers,
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Conexão: SUCESSO")
            print(f"   Database: {result.get('database', 'N/A')}")
            print(f"   Host: {result.get('host', 'N/A')}")
        else:
            print("❌ Conexão: ERRO")
            return False
    except Exception as e:
        print(f"❌ Conexão: ERRO - {e}")
        return False

    # Passo 2: Preview dos dados
    print("\n2️⃣ Fazendo preview...")
    sql_query = """
    SELECT
        produto_id,
        descricao_produto,
        codigo_produto,
        codigo_barra,
        ncm,
        cest
    FROM dbo.produto
    WHERE descricao_produto IS NOT NULL
    """

    try:
        response = requests.post(
            "http://localhost:8000/api/import/preview",
            json=connection_data,
            params={"sql_query": sql_query, "limit": 50},
            headers=headers,
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Preview: SUCESSO")
            print(f"   Registros: {result.get('preview_count', 0)}")
            print(f"   Colunas: {len(result.get('columns', []))}")
        else:
            print("❌ Preview: ERRO")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Preview: ERRO - {e}")
        return False

    print("\n✅ FLUXO COMPLETO: FUNCIONANDO!")
    return True


if __name__ == "__main__":
    success1 = test_frontend_import_correctly()
    success2 = simulate_full_frontend_flow()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 TODOS OS TESTES: APROVADOS!")
        print("✅ O problema de importação está RESOLVIDO!")
    else:
        print("❌ Ainda há problemas a resolver")
    print("=" * 50)
