#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo Completo de Extração de Dados
=====================================

Este script demonstra como usar o módulo de extração de dados
para implementar uma funcionalidade completa de importação.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from auditoria_icms.data_processing.data_extractor import (
    DataExtractor, 
    DatabaseConfig, 
    ExtractionConfig
)
import pandas as pd
import json
from datetime import datetime

def exemplo_extracao_completa():
    """
    Exemplo completo de extração e processamento de dados
    """
    print("🚀 Exemplo Completo de Extração de Dados")
    print("=" * 60)
    
    # 1. Configuração da conexão
    print("\n🔧 Etapa 1: Configuração da Conexão")
    print("-" * 40)
    
    config = DatabaseConfig(
        host="localhost",
        port="5432",
        database="db_04565289005297", 
        user="postgres",
        password="sefin",
        schema="dbo",
        db_type="postgresql"
    )
    
    print(f"📋 Configuração:")
    print(f"   - Tipo: {config.db_type}")
    print(f"   - Host: {config.host}:{config.port}")
    print(f"   - Banco: {config.database}")
    print(f"   - Schema: {config.schema}")
    print(f"   - Usuário: {config.user}")
    
    # 2. Testar conexão
    print("\n🔧 Etapa 2: Teste de Conexão")
    print("-" * 40)
    
    extractor = DataExtractor(config)
    
    test_result = extractor.test_connection()
    if test_result["success"]:
        print("✅ Conexão estabelecida com sucesso!")
        print(f"📋 Info: {test_result['database_info']}")
    else:
        print(f"❌ Falha na conexão: {test_result['error']}")
        return
    
    # 3. Obter informações da tabela
    print("\n🔧 Etapa 3: Informações da Tabela")
    print("-" * 40)
    
    table_info = extractor.get_table_info("produto")
    if table_info["success"]:
        print(f"✅ Tabela 'produto' encontrada!")
        print(f"📊 Total de registros: {table_info['total_records']:,}")
        print(f"🏛️ Número de colunas: {len(table_info['columns'])}")
        
        print(f"\n📋 Principais colunas:")
        main_columns = ['produto_id', 'descricao_produto', 'codigo_produto', 'ncm', 'cest']
        for col_info in table_info['columns']:
            if col_info['column_name'] in main_columns:
                print(f"   - {col_info['column_name']} ({col_info['data_type']})")
    else:
        print(f"❌ Erro: {table_info['error']}")
        return
    
    # 4. Preview dos dados
    print("\n🔧 Etapa 4: Preview dos Dados")
    print("-" * 40)
    
    extraction_config = ExtractionConfig(
        table_name='produto',
        columns=[
            'produto_id',
            'descricao_produto', 
            'codigo_produto',
            'codigo_barra',
            'ncm',
            'cest'
        ]
    )
    
    preview = extractor.preview_data(extraction_config, limit=5)
    if preview["success"]:
        print(f"✅ Preview realizado!")
        print(f"📊 Registros no preview: {preview['preview_count']}")
        
        print(f"\n🎯 Amostra dos dados:")
        for i, record in enumerate(preview['data'], 1):
            print(f"\n   📄 Registro {i}:")
            print(f"      ID: {record.get('produto_id')}")
            print(f"      Descrição: {record.get('descricao_produto', '')[:50]}...")
            print(f"      Código: {record.get('codigo_produto', 'N/A')}")
            print(f"      NCM: {record.get('ncm', 'N/A')}")
            print(f"      CEST: {record.get('cest', 'N/A')}")
    else:
        print(f"❌ Erro no preview: {preview['error']}")
    
    # 5. Extração de dados (amostra)
    print("\n🔧 Etapa 5: Extração de Amostra")
    print("-" * 40)
    
    # Configurar para extrair apenas uma amostra
    extraction_config.limit = 500
    
    df = extractor.extract_data(extraction_config)
    
    if df is not None and not df.empty:
        print(f"✅ Extração realizada com sucesso!")
        print(f"📊 Registros extraídos: {len(df):,}")
        
        print(f"\n📈 Estatísticas dos dados:")
        print(f"   - Registros com descrição válida: {df['descricao_produto'].notna().sum():,}")
        if 'ncm' in df.columns:
            print(f"   - Registros com NCM: {df['ncm'].notna().sum():,}")
        if 'cest' in df.columns:
            print(f"   - Registros com CEST: {df['cest'].notna().sum():,}")
        
        print(f"\n🎯 Exemplos de produtos extraídos:")
        sample_df = df[df['descricao_produto'].notna()].head(3)
        for idx, row in sample_df.iterrows():
            print(f"\n   📦 Produto {idx + 1}:")
            print(f"      Descrição: {row['descricao_produto']}")
            print(f"      NCM: {row.get('ncm', 'N/A')}")
            print(f"      CEST: {row.get('cest', 'N/A')}")
        
        # 6. Salvar dados extraídos
        print("\n🔧 Etapa 6: Salvamento dos Dados")
        print("-" * 40)
        
        # Salvar como CSV
        csv_filename = f"dados_extraidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"✅ Dados salvos em: {csv_filename}")
        
        # Salvar estatísticas como JSON
        stats = {
            "total_registros": len(df),
            "registros_com_descricao": int(df['descricao_produto'].notna().sum()),
            "registros_com_ncm": int(df['ncm'].notna().sum()) if 'ncm' in df.columns else 0,
            "registros_com_cest": int(df['cest'].notna().sum()) if 'cest' in df.columns else 0,
            "data_extracao": datetime.now().isoformat(),
            "configuracao": {
                "banco": config.database,
                "tabela": extraction_config.table_name,
                "limite": extraction_config.limit
            }
        }
        
        stats_filename = f"estatisticas_extracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✅ Estatísticas salvas em: {stats_filename}")
        
    else:
        print("❌ Nenhum dado foi extraído")
    
    # 7. Finalização
    print("\n🔧 Etapa 7: Finalização")
    print("-" * 40)
    
    extractor.close()
    print("✅ Conexão fechada")
    
    print("\n🎉 Exemplo completo finalizado com sucesso!")
    print("=" * 60)
    
    return True

def exemplo_simulacao_api():
    """
    Simula o funcionamento da API de importação
    """
    print("\n🚀 Simulação da API de Importação")
    print("=" * 60)
    
    # Simular requisições da API
    connection_config = {
        "type": "postgresql",
        "host": "localhost", 
        "port": 5432,
        "database": "db_04565289005297",
        "user": "postgres",
        "password": "sefin",
        "schema": "dbo"
    }
    
    print("🔄 Simulando POST /api/import/test-connection")
    print("-" * 50)
    
    # Converter para configuração do extrator
    db_config = DatabaseConfig(
        host=connection_config["host"],
        port=str(connection_config["port"]), 
        database=connection_config["database"],
        user=connection_config["user"],
        password=connection_config["password"],
        schema=connection_config["schema"],
        db_type=connection_config["type"]
    )
    
    extractor = DataExtractor(db_config)
    test_result = extractor.test_connection()
    
    print(f"📋 Resposta da API (test-connection):")
    print(json.dumps(test_result, indent=2, ensure_ascii=False))
    
    if test_result["success"]:
        print("\n🔄 Simulando POST /api/import/preview")
        print("-" * 50)
        
        # Preview dos dados
        extraction_config = ExtractionConfig(
            table_name='produto',
            columns=['produto_id', 'descricao_produto', 'ncm', 'cest']
        )
        
        preview = extractor.preview_data(extraction_config, limit=3)
        
        print(f"📋 Resposta da API (preview):")
        print(json.dumps(preview, indent=2, ensure_ascii=False, default=str))
    
    extractor.close()
    
    print("\n✅ Simulação da API concluída!")

if __name__ == "__main__":
    print("🎯 Demonstração Completa do Sistema de Extração")
    print("=" * 70)
    
    try:
        # Executar exemplo completo
        success = exemplo_extracao_completa()
        
        if success:
            # Simular API
            exemplo_simulacao_api()
        
        print("\n🏆 Demonstração finalizada com sucesso!")
        print("=" * 70)
        
        print("\n📚 Resumo do que foi implementado:")
        print("✅ Módulo de extração de dados robusto")
        print("✅ Suporte a PostgreSQL, SQL Server e MySQL")
        print("✅ Configuração via arquivo .env")
        print("✅ Testes de conexão e preview de dados")
        print("✅ Extração com limpeza automática")
        print("✅ Salvamento em CSV e estatísticas em JSON")
        print("✅ Integração preparada para API FastAPI")
        
        print("\n🎯 Próximos passos sugeridos:")
        print("1. Resolver problema de finalização da API")
        print("2. Testar interface React com backend corrigido")
        print("3. Implementar importação completa via interface web")
        print("4. Adicionar validação e mapeamento de dados")
        print("5. Criar relatórios de importação")
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")
        import traceback
        traceback.print_exc()
