"""
Script de Execução - Fase 6
Demonstração e teste do sistema integrado completo
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phase6_execution.log')
    ]
)

logger = logging.getLogger(__name__)


async def run_phase6_demo():
    """Executa demonstração completa da Fase 6"""
    logger.info("🚀 Iniciando demonstração da Fase 6 - Sistema Integrado")
    
    try:
        # Importar componentes (simulado - adaptaria imports conforme estrutura)
        from src.auditoria_icms.phase6_integrated_system import IntegratedSystem
        
        # 1. Inicializar sistema
        logger.info("🔧 Inicializando sistema integrado...")
        system = IntegratedSystem()
        
        # 2. Verificar status inicial
        logger.info("📊 Verificando status do sistema...")
        initial_status = system.check_system_status()
        
        print("\n" + "="*50)
        print("📋 STATUS INICIAL DO SISTEMA")
        print("="*50)
        print(f"Database Ready: {'✅' if initial_status.database_ready else '❌'}")
        print(f"Agents Ready: {'✅' if initial_status.agents_ready else '❌'}")
        print(f"Workflows Ready: {'✅' if initial_status.workflows_ready else '❌'}")
        print(f"Data Imported: {'✅' if initial_status.data_imported else '❌'}")
        
        if initial_status.errors:
            print("\n🚨 Erros encontrados:")
            for error in initial_status.errors:
                print(f"  - {error}")
        
        if initial_status.warnings:
            print("\n⚠️ Avisos:")
            for warning in initial_status.warnings:
                print(f"  - {warning}")
        
        # 3. Configurar sistema se necessário
        if not all([initial_status.database_ready, initial_status.agents_ready, initial_status.workflows_ready]):
            logger.info("🔧 Configurando sistema...")
            setup_success = system.setup_complete_system()
            
            if setup_success:
                print("\n✅ Sistema configurado com sucesso!")
            else:
                print("\n❌ Falha na configuração do sistema")
                return False
        
        # 4. Demonstrar processamento de produtos (simulação)
        logger.info("📋 Demonstrando processamento de produtos...")
        await demonstrate_product_processing(system)
        
        # 5. Gerar relatório final
        logger.info("📊 Gerando relatório final...")
        final_report = system.generate_system_report()
        
        print("\n" + "="*50)
        print("📊 RELATÓRIO FINAL DO SISTEMA")
        print("="*50)
        print(json.dumps(final_report, indent=2, ensure_ascii=False, default=str))
        
        return True
        
    except ImportError as e:
        logger.error(f"Erro de importação: {e}")
        print(f"\n❌ Erro de importação: {e}")
        print("💡 Certifique-se de que todos os módulos estão no PYTHONPATH")
        return False
        
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
        print(f"\n❌ Erro na demonstração: {e}")
        return False


async def demonstrate_product_processing(system):
    """Demonstra processamento de produtos"""
    try:
        # Dados de exemplo para teste
        test_products = [
            {
                "id": 1,
                "codigo_produto": "PROC001",
                "descricao": "Processador Intel Core i7",
                "ncm": "84713012",
                "empresa_id": 1
            },
            {
                "id": 2,
                "codigo_produto": "MED001", 
                "descricao": "Paracetamol 500mg",
                "ncm": "30049099",
                "empresa_id": 1
            },
            {
                "id": 3,
                "codigo_produto": "AUTO001",
                "descricao": "Filtro de óleo automotivo",
                "ncm": "",  # Sem NCM para testar determinação
                "empresa_id": 1
            }
        ]
        
        test_empresa_info = {
            "cnpj": "12345678000123",
            "razao_social": "Empresa Teste LTDA",
            "atividade": "Comercio varejista de equipamentos de informatica",
            "regime_tributario": "Lucro Presumido"
        }
        
        print("\n" + "="*50)
        print("🧪 DEMONSTRAÇÃO DE PROCESSAMENTO")
        print("="*50)
        
        # Simular processamento (adaptaria para usar métodos reais)
        for i, product in enumerate(test_products, 1):
            print(f"\n📦 Produto {i}: {product['descricao']}")
            print(f"   Código: {product['codigo_produto']}")
            print(f"   NCM: {product['ncm'] or 'Não informado'}")
            
            # Simular enriquecimento
            try:
                enrichment_result = system.enrichment_agent.enrich_product_data(
                    product, test_empresa_info
                )
                
                print(f"   Resultado: {'✅ Sucesso' if enrichment_result.success else '❌ Falha'}")
                print(f"   Confiança: {enrichment_result.confidence:.2%}")
                
                if enrichment_result.changes:
                    print("   Mudanças:")
                    for change in enrichment_result.changes:
                        print(f"     - {change['field']}: {change['action']}")
                
                if enrichment_result.warnings:
                    print("   Avisos:")
                    for warning in enrichment_result.warnings:
                        print(f"     ⚠️ {warning}")
                        
            except Exception as e:
                print(f"   ❌ Erro no processamento: {e}")
        
        print("\n✅ Demonstração de processamento concluída")
        
    except Exception as e:
        logger.error(f"Erro na demonstração de processamento: {e}")
        print(f"\n❌ Erro na demonstração: {e}")


def run_agent_tests():
    """Executa testes dos agentes individuais"""
    print("\n" + "="*50)
    print("🧪 TESTES DOS AGENTES")
    print("="*50)
    
    try:
        from src.auditoria_icms.agents.real_agents import NCMAgent, CESTAgent
        from src.auditoria_icms.agents.data_agents import EnrichmentAgent
        
        # Teste do agente NCM
        print("\n🤖 Testando Agente NCM...")
        ncm_agent = NCMAgent()
        
        ncm_test_result = ncm_agent.validate_ncm(
            ncm_code="84713012",
            description="Processador Intel Core i7",
            empresa_atividade="informatica"
        )
        
        print(f"   Resultado: {'✅' if ncm_test_result.get('valid') else '❌'}")
        print(f"   Confiança: {ncm_test_result.get('confidence', 0):.2%}")
        
        # Teste do agente CEST
        print("\n🤖 Testando Agente CEST...")
        cest_agent = CESTAgent()
        
        cest_test_result = cest_agent.determine_cest(
            ncm_code="84713012",
            description="Processador Intel Core i7",
            empresa_atividade="informatica"
        )
        
        print(f"   Resultado: {'✅' if cest_test_result.get('success') else '❌'}")
        print(f"   CEST: {cest_test_result.get('cest_determinado', 'Não aplicável')}")
        
        # Teste do agente de enriquecimento
        print("\n🤖 Testando Agente de Enriquecimento...")
        enrichment_agent = EnrichmentAgent()
        
        test_product = {
            "codigo_produto": "TEST001",
            "descricao": "Processador Intel Core i7",
            "ncm": "84713012",
            "empresa_id": 1
        }
        
        enrichment_result = enrichment_agent.enrich_product_data(test_product)
        
        print(f"   Resultado: {'✅' if enrichment_result.success else '❌'}")
        print(f"   Confiança: {enrichment_result.confidence:.2%}")
        print(f"   Mudanças: {len(enrichment_result.changes)}")
        
        print("\n✅ Testes dos agentes concluídos")
        
    except ImportError as e:
        print(f"\n❌ Erro de importação nos testes: {e}")
    except Exception as e:
        print(f"\n❌ Erro nos testes dos agentes: {e}")


def run_database_tests():
    """Executa testes do banco de dados"""
    print("\n" + "="*50)
    print("🗄️ TESTES DO BANCO DE DADOS")
    print("="*50)
    
    try:
        from src.auditoria_icms.database.postgresql_setup import PostgreSQLSetup
        
        db_setup = PostgreSQLSetup()
        
        # Teste de conexão
        print("\n🔌 Testando conexão...")
        connection_ok = db_setup.test_connection()
        print(f"   Conexão: {'✅' if connection_ok else '❌'}")
        
        if connection_ok:
            # Estatísticas do banco
            print("\n📊 Obtendo estatísticas...")
            stats = db_setup.get_database_stats()
            
            if stats:
                print("   Estatísticas:")
                for key, value in stats.items():
                    if isinstance(value, dict):
                        print(f"     {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"       {sub_key}: {sub_value}")
                    else:
                        print(f"     {key}: {value}")
            else:
                print("   ⚠️ Não foi possível obter estatísticas")
        
        print("\n✅ Testes do banco de dados concluídos")
        
    except ImportError as e:
        print(f"\n❌ Erro de importação nos testes de BD: {e}")
    except Exception as e:
        print(f"\n❌ Erro nos testes do banco: {e}")


def main():
    """Função principal"""
    print("🎯 SISTEMA DE AUDITORIA FISCAL ICMS - FASE 6")
    print("=" * 60)
    print("Sistema Integrado com PostgreSQL + Agentes Reais")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test-agents":
            run_agent_tests()
        elif command == "test-db":
            run_database_tests()
        elif command == "demo":
            asyncio.run(run_phase6_demo())
        elif command == "setup":
            # Apenas configuração
            try:
                from src.auditoria_icms.phase6_integrated_system import IntegratedSystem
                system = IntegratedSystem()
                success = system.setup_complete_system()
                print(f"\n{'✅ Configuração concluída' if success else '❌ Falha na configuração'}")
            except Exception as e:
                print(f"\n❌ Erro na configuração: {e}")
        else:
            print(f"\n❌ Comando desconhecido: {command}")
            print_usage()
    else:
        # Execução completa
        print("\n🚀 Executando demonstração completa...")
        success = asyncio.run(run_phase6_demo())
        
        if success:
            print("\n🎉 Demonstração da Fase 6 concluída com sucesso!")
        else:
            print("\n💥 Demonstração falhou - verifique os logs")


def print_usage():
    """Imprime instruções de uso"""
    print("\nUso:")
    print("  python run_phase6.py                # Demonstração completa")
    print("  python run_phase6.py demo          # Demonstração completa")
    print("  python run_phase6.py setup         # Apenas configuração")
    print("  python run_phase6.py test-agents   # Testar agentes")
    print("  python run_phase6.py test-db       # Testar banco de dados")


if __name__ == "__main__":
    main()
