"""
Demonstração Simplificada - Sistema de Auditoria Fiscal ICMS Fase 2
Versão independente sem dependências externas
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Adiciona o diretório src ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIngestionSimulada:
    """Simulação da classe EmpresaDataIngestion para demonstração"""
    
    def __init__(self, empresa_id: int, db_config: Dict[str, Any]):
        self.empresa_id = empresa_id
        self.db_config = db_config
        logger.info(f"DataIngestion simulada criada para empresa {empresa_id}")
    
    def test_connection(self) -> bool:
        """Simula teste de conexão"""
        logger.info(f"Testando conexão com {self.db_config['database_type']}")
        return True
    
    def update_produtos_processados(self, produtos: List[Dict[str, Any]]) -> bool:
        """Simula atualização de produtos processados"""
        logger.info(f"Simulando atualização de {len(produtos)} produtos")
        return True

class FiscalAuditDemoSimple:
    """
    Demonstração simplificada do Sistema de Auditoria Fiscal ICMS Fase 2
    """
    
    def __init__(self):
        # Configurações de exemplo
        self.empresa_configs = {
            1: {
                'nome': 'Empresa Alpha Ltda',
                'db_config': {
                    'database_type': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'empresa_alpha',
                    'username': 'user_alpha',
                    'password': 'pass_alpha'
                }
            },
            2: {
                'nome': 'Beta Corporation',
                'db_config': {
                    'database_type': 'sql_server',
                    'host': 'servidor-beta.com',
                    'port': 1433,
                    'database': 'ERP_Beta',
                    'username': 'auditor_beta',
                    'password': 'senha_beta'
                }
            },
            3: {
                'nome': 'Gamma Industries',
                'db_config': {
                    'database_type': 'oracle',
                    'host': 'oracle-gamma.local',
                    'port': 1521,
                    'database': 'GAMMA_PROD',
                    'username': 'gamma_audit',
                    'password': 'oracle_123'
                }
            }
        }
        
        # Configurações de processamento
        self.processing_config = {
            'confianca_minima': 0.7,
            'auto_approve_threshold': 0.9,
            'max_retries': 3,
            'timeout_agente': 300,
            'batch_size': 50
        }
        
        # Produtos de exemplo para teste
        self.produtos_exemplo = [
            {
                'produto_id': 'PROD001',
                'codigo_produto': 'ABC123',
                'descricao_produto': 'Smartphone Samsung Galaxy A54 128GB Preto',
                'codigo_barra': '7891234567890',
                'ncm': None,
                'cest': None
            },
            {
                'produto_id': 'PROD002',
                'codigo_produto': 'DEF456',
                'descricao_produto': 'Notebook Dell Inspiron 15 Intel i5 8GB 256GB SSD',
                'codigo_barra': '7891234567891',
                'ncm': '84713012',  # NCM existente para confirmação
                'cest': None
            },
            {
                'produto_id': 'PROD003',
                'codigo_produto': 'GHI789',
                'descricao_produto': 'Cafeteira Elétrica Philco PH41 Preta 1.2L',
                'codigo_barra': '7891234567892',
                'ncm': None,
                'cest': '13.014.00'  # CEST existente para confirmação
            },
            {
                'produto_id': 'PROD004',
                'codigo_produto': 'JKL012',
                'descricao_produto': 'Tênis Nike Air Max 90 Masculino Branco',
                'codigo_barra': '7891234567893',
                'ncm': '64039900',
                'cest': '13.018.00'
            },
            {
                'produto_id': 'PROD005',
                'codigo_produto': 'MNO345',
                'descricao_produto': 'Geladeira Brastemp Frost Free Duplex 400L Inox',
                'codigo_barra': '7891234567894',
                'ncm': None,
                'cest': None
            }
        ]
    
    def executar_demonstracao_completa(self):
        """Executa demonstração completa do sistema"""
        
        print("=" * 80)
        print("SISTEMA DE AUDITORIA FISCAL ICMS - FASE 2")
        print("Demonstração Multi-Tenant com Processamento de Agentes")
        print("Versão Simplificada para Demonstração")
        print("=" * 80)
        
        # 1. Demonstração da conexão com bancos
        print("\n1. TESTANDO CONEXÕES COM BANCOS DAS EMPRESAS")
        print("-" * 50)
        self._demonstrar_conexoes_banco()
        
        # 2. Demonstração do processamento individual
        print("\n2. PROCESSAMENTO INDIVIDUAL DE PRODUTOS")
        print("-" * 50)
        self._demonstrar_processamento_individual()
        
        # 3. Demonstração do processamento em lote
        print("\n3. PROCESSAMENTO EM LOTE")
        print("-" * 50)
        self._demonstrar_processamento_lote()
        
        # 4. Demonstração de workflow multi-estado
        print("\n4. WORKFLOW MULTI-ESTADO")
        print("-" * 50)
        self._demonstrar_workflow_estados()
        
        # 5. Relatório de auditoria
        print("\n5. RELATÓRIO DE AUDITORIA")
        print("-" * 50)
        self._gerar_relatorio_auditoria()
        
        print("\n" + "=" * 80)
        print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("Sistema pronto para implementação das Fases 2 e 3")
        print("=" * 80)
    
    def _demonstrar_conexoes_banco(self):
        """Demonstra conexões com bancos das empresas"""
        
        for empresa_id, config in self.empresa_configs.items():
            print(f"\nEmpresa {empresa_id}: {config['nome']}")
            print(f"Tipo de banco: {config['db_config']['database_type']}")
            
            try:
                # Simula criação da instância de ingestão
                data_ingestion = DataIngestionSimulada(empresa_id, config['db_config'])
                
                # Simula teste de conexão
                conexao_ok = data_ingestion.test_connection()
                
                if conexao_ok:
                    print(f"✓ Conexão estabelecida com sucesso")
                    print(f"  Host: {config['db_config']['host']}")
                    print(f"  Database: {config['db_config']['database']}")
                    print(f"  Produtos encontrados: {len(self.produtos_exemplo)} (simulado)")
                else:
                    print(f"✗ Erro na conexão")
                
            except Exception as e:
                print(f"✗ Erro na conexão: {str(e)}")
    
    def _demonstrar_processamento_individual(self):
        """Demonstra processamento individual de produtos"""
        
        try:
            # Importa os módulos simplificados
            from auditoria_icms.agents.manager_agent_simple import ManagerAgent
            
            empresa_id = 1
            config_empresa = self.empresa_configs[empresa_id]
            
            print(f"\nProcessando produtos da {config_empresa['nome']}")
            
            # Cria manager agent para a empresa
            data_ingestion = DataIngestionSimulada(empresa_id, config_empresa['db_config'])
            manager = ManagerAgent(empresa_id, data_ingestion, self.processing_config)
            
            for produto_data in self.produtos_exemplo[:2]:  # Processa apenas 2 produtos
                print(f"\n--- Produto: {produto_data['codigo_produto']} ---")
                print(f"Descrição: {produto_data['descricao_produto']}")
                print(f"NCM atual: {produto_data['ncm'] or 'Não definido'}")
                print(f"CEST atual: {produto_data['cest'] or 'Não definido'}")
                
                # Processa produto usando o método process da classe base
                resultado_dict = manager.process(produto_data)
                
                # Exibe resultado
                print(f"\nResultado do processamento:")
                print(f"Status: {resultado_dict['status']}")
                print(f"Tempo execução: {resultado_dict['tempo_execucao']:.2f}s")
                print(f"Confiança média: {resultado_dict['confianca_media']:.2%}")
                
                if resultado_dict.get('erro_detalhes'):
                    print(f"Erro: {resultado_dict['erro_detalhes']}")
                
                # Mostra alguns logs dos agentes
                logs = resultado_dict.get('logs_agentes', [])
                if logs:
                    print(f"Agentes executados: {len(logs)}")
                    for log in logs[:2]:  # Mostra apenas os primeiros 2
                        print(f"  - {log['agente_nome']}: {log['status']}")
                        
        except ImportError as e:
            print(f"Erro de importação: {e}")
            print("Executando simulação simplificada...")
            self._simular_processamento_individual()
    
    def _simular_processamento_individual(self):
        """Simulação de processamento individual quando imports falham"""
        
        for produto_data in self.produtos_exemplo[:2]:
            print(f"\n--- Produto: {produto_data['codigo_produto']} ---")
            print(f"Descrição: {produto_data['descricao_produto']}")
            
            # Simula processamento
            print("Executando agentes:")
            print("  ✓ EnrichmentAgent: Sucesso (confiança: 85%)")
            print("  ✓ NCMAgent: Sucesso (confiança: 90%)")
            print("  ✓ CESTAgent: Sucesso (confiança: 85%)")
            print("  ✓ ReconciliationAgent: Sucesso (confiança: 88%)")
            
            print(f"NCM sugerido: 12345678")
            print(f"CEST sugerido: 12.345.67")
            print(f"Status: Aprovado automaticamente")
    
    def _demonstrar_processamento_lote(self):
        """Demonstra processamento em lote"""
        
        try:
            from auditoria_icms.agents.manager_agent_simple import ManagerAgent
            
            empresa_id = 2
            config_empresa = self.empresa_configs[empresa_id]
            
            print(f"\nProcessamento em lote - {config_empresa['nome']}")
            
            # Cria manager agent para a empresa
            data_ingestion = DataIngestionSimulada(empresa_id, config_empresa['db_config'])
            manager = ManagerAgent(empresa_id, data_ingestion, self.processing_config)
            
            # Cria lista de produtos simulados
            produtos = [manager._criar_produto_from_dict(p) for p in self.produtos_exemplo]
            
            print(f"Produtos para processar: {len(produtos)}")
            
            # Processa lote
            resultado_lote = manager.processar_lote(produtos)
            
            # Exibe resultados
            print(f"\nResultados do processamento em lote:")
            print(f"Task ID: {resultado_lote.task_id}")
            print(f"Total produtos: {resultado_lote.total_produtos}")
            print(f"Processados: {resultado_lote.produtos_processados}")
            print(f"Sucesso: {resultado_lote.produtos_com_sucesso}")
            print(f"Erro: {resultado_lote.produtos_com_erro}")
            print(f"Revisão pendente: {resultado_lote.produtos_pendente_revisao}")
            print(f"Tempo total: {resultado_lote.tempo_total:.2f}s")
            
            # Taxa de sucesso
            if resultado_lote.total_produtos > 0:
                taxa_sucesso = (resultado_lote.produtos_com_sucesso / resultado_lote.total_produtos) * 100
                print(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
                
        except ImportError:
            print("Simulando processamento em lote...")
            self._simular_processamento_lote()
    
    def _simular_processamento_lote(self):
        """Simulação de processamento em lote"""
        
        print(f"Produtos para processar: {len(self.produtos_exemplo)}")
        print("Processando lote...")
        
        import time
        for i, produto in enumerate(self.produtos_exemplo):
            print(f"  Processando {i+1}/{len(self.produtos_exemplo)}: {produto['codigo_produto']}")
            time.sleep(0.2)  # Simula tempo de processamento
        
        print("\nResultados simulados:")
        print(f"Total produtos: {len(self.produtos_exemplo)}")
        print(f"Sucesso: 4")
        print(f"Erro: 1")
        print(f"Revisão pendente: 0")
        print(f"Taxa de sucesso: 80.0%")
    
    def _demonstrar_workflow_estados(self):
        """Demonstra workflow com diferentes estados"""
        
        print("\nDemonstrando transições de estado no workflow:")
        
        estados = [
            'PENDENTE',
            'ENRIQUECENDO',
            'ENRIQUECIDO', 
            'CLASSIFICANDO_NCM',
            'NCM_CLASSIFICADO',
            'CLASSIFICANDO_CEST',
            'CEST_CLASSIFICADO',
            'RECONCILIANDO',
            'CONCLUIDO'
        ]
        
        produto_exemplo = self.produtos_exemplo[0]
        print(f"\nProduto: {produto_exemplo['descricao_produto'][:50]}...")
        
        import time
        for i, estado in enumerate(estados):
            print(f"  {i+1}. {estado}")
            time.sleep(0.3)  # Simula transição entre estados
        
        print("\n✓ Workflow concluído com sucesso!")
        print("  NCM final: 12345678 (confiança: 90%)")
        print("  CEST final: 12.345.67 (confiança: 85%)")
        print("  Status: Aprovado automaticamente")
    
    def _gerar_relatorio_auditoria(self):
        """Gera relatório de auditoria consolidado"""
        
        print("\nRELATÓRIO DE AUDITORIA CONSOLIDADO")
        print("-" * 40)
        
        # Simula dados de auditoria
        relatorio = {
            'data_geracao': datetime.utcnow().isoformat(),
            'versao_sistema': 'Fase 2 - Multi-tenant',
            'empresas_processadas': len(self.empresa_configs),
            'total_produtos': len(self.produtos_exemplo) * len(self.empresa_configs),
            'produtos_com_sucesso': 12,
            'produtos_com_erro': 2,
            'produtos_revisao_pendente': 1,
            'tempo_total_processamento': 45.6,
            'taxa_sucesso_geral': 80.0,
            'melhorias_implementadas': [
                'Sistema multi-tenant',
                'Conexão com bancos externos',
                'Workflow com LangGraph',
                'Auditoria completa de agentes',
                'Processamento em lote otimizado'
            ],
            'estatisticas_por_empresa': {}
        }
        
        # Estatísticas por empresa
        for empresa_id, config in self.empresa_configs.items():
            relatorio['estatisticas_por_empresa'][empresa_id] = {
                'nome': config['nome'],
                'produtos_processados': len(self.produtos_exemplo),
                'taxa_sucesso': 85.0,
                'tempo_medio_produto': 2.3,
                'tipos_banco': config['db_config']['database_type']
            }
        
        # Exibe relatório
        print(f"Data de geração: {relatorio['data_geracao']}")
        print(f"Versão do sistema: {relatorio['versao_sistema']}")
        print(f"Empresas processadas: {relatorio['empresas_processadas']}")
        print(f"Total de produtos: {relatorio['total_produtos']}")
        print(f"Taxa de sucesso geral: {relatorio['taxa_sucesso_geral']:.1f}%")
        print(f"Tempo total: {relatorio['tempo_total_processamento']:.1f}s")
        
        print(f"\nMelhorias implementadas na Fase 2:")
        for melhoria in relatorio['melhorias_implementadas']:
            print(f"  ✓ {melhoria}")
        
        print(f"\nEstatísticas por empresa:")
        for empresa_id, stats in relatorio['estatisticas_por_empresa'].items():
            print(f"  {empresa_id}. {stats['nome']} ({stats['tipos_banco']})")
            print(f"     Produtos: {stats['produtos_processados']}, Sucesso: {stats['taxa_sucesso']:.1f}%")
        
        # Salva relatório em arquivo
        relatorio_file = 'relatorio_auditoria_fase2_demo.json'
        try:
            with open(relatorio_file, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Relatório salvo em: {relatorio_file}")
        except Exception as e:
            print(f"⚠ Aviso: Não foi possível salvar relatório: {str(e)}")

def main():
    """Função principal da demonstração"""
    
    try:
        demo = FiscalAuditDemoSimple()
        demo.executar_demonstracao_completa()
        
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
        
    except Exception as e:
        print(f"\nErro na demonstração: {str(e)}")
        logger.error(f"Erro na demonstração: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
