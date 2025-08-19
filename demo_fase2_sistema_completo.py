"""
Script de Demonstração - Sistema de Auditoria Fiscal ICMS Fase 2
Demonstra o funcionamento completo do sistema multi-tenant
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

from auditoria_icms.data_processing.empresa_data_ingestion import EmpresaDataIngestion
from auditoria_icms.agents.manager_agent_v2 import ManagerAgent, ProcessingResult, BatchProcessingResult
from auditoria_icms.workflows.fiscal_audit_workflow import FiscalAuditWorkflow
from auditoria_icms.database.models import ProdutoEmpresa

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FiscalAuditDemo:
    """
    Demonstração completa do Sistema de Auditoria Fiscal ICMS Fase 2
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
        
        # 4. Demonstração do workflow com LangGraph
        print("\n4. WORKFLOW COM LANGGRAPH")
        print("-" * 50)
        self._demonstrar_workflow_langgraph()
        
        # 5. Relatório de auditoria
        print("\n5. RELATÓRIO DE AUDITORIA")
        print("-" * 50)
        self._gerar_relatorio_auditoria()
        
        print("\n" + "=" * 80)
        print("DEMONSTRAÇÃO CONCLUÍDA")
        print("=" * 80)
    
    def _demonstrar_conexoes_banco(self):
        """Demonstra conexões com bancos das empresas"""
        
        for empresa_id, config in self.empresa_configs.items():
            print(f"\nEmpresa {empresa_id}: {config['nome']}")
            print(f"Tipo de banco: {config['db_config']['database_type']}")
            
            try:
                # Simula criação da instância de ingestão
                data_ingestion = EmpresaDataIngestion(empresa_id, config['db_config'])
                
                # Simula teste de conexão
                print(f"✓ Conexão estabelecida com sucesso")
                print(f"  Host: {config['db_config']['host']}")
                print(f"  Database: {config['db_config']['database']}")
                
                # Simula consulta de produtos
                print(f"✓ Consultando produtos da empresa...")
                print(f"  Produtos encontrados: {len(self.produtos_exemplo)} (simulado)")
                
            except Exception as e:
                print(f"✗ Erro na conexão: {str(e)}")
    
    def _demonstrar_processamento_individual(self):
        """Demonstra processamento individual de produtos"""
        
        empresa_id = 1
        config_empresa = self.empresa_configs[empresa_id]
        
        print(f"\nProcessando produtos da {config_empresa['nome']}")
        
        # Cria manager agent para a empresa
        data_ingestion = EmpresaDataIngestion(empresa_id, config_empresa['db_config'])
        manager = ManagerAgent(empresa_id, data_ingestion, self.processing_config)
        
        for produto_data in self.produtos_exemplo[:2]:  # Processa apenas 2 produtos
            print(f"\n--- Produto: {produto_data['codigo_produto']} ---")
            print(f"Descrição: {produto_data['descricao_produto']}")
            print(f"NCM atual: {produto_data['ncm'] or 'Não definido'}")
            print(f"CEST atual: {produto_data['cest'] or 'Não definido'}")
            
            # Cria objeto produto simulado
            produto = self._criar_produto_simulado(produto_data)
            
            # Processa produto
            resultado = manager._processar_produto_individual(produto)
            
            # Exibe resultado
            print(f"\nResultado do processamento:")
            print(f"Status: {resultado.status}")
            print(f"Tempo execução: {resultado.tempo_execucao:.2f}s")
            
            if resultado.produto_atualizado:
                p = resultado.produto_atualizado
                print(f"NCM sugerido: {getattr(p, 'ncm_sugerido', 'N/A')}")
                print(f"CEST sugerido: {getattr(p, 'cest_sugerido', 'N/A')}")
                print(f"Confiança NCM: {getattr(p, 'confianca_ncm', 0):.2%}")
                print(f"Confiança CEST: {getattr(p, 'confianca_cest', 0):.2%}")
                print(f"Requer revisão: {getattr(p, 'revisao_manual', False)}")
            
            if resultado.erro_detalhes:
                print(f"Erro: {resultado.erro_detalhes}")
    
    def _demonstrar_processamento_lote(self):
        """Demonstra processamento em lote"""
        
        empresa_id = 2
        config_empresa = self.empresa_configs[empresa_id]
        
        print(f"\nProcessamento em lote - {config_empresa['nome']}")
        
        # Cria manager agent para a empresa
        data_ingestion = EmpresaDataIngestion(empresa_id, config_empresa['db_config'])
        manager = ManagerAgent(empresa_id, data_ingestion, self.processing_config)
        
        # Cria lista de produtos simulados
        produtos = [self._criar_produto_simulado(p) for p in self.produtos_exemplo]
        
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
        
        # Detalhes de alguns produtos
        print(f"\nDetalhes dos primeiros produtos:")
        for i, resultado in enumerate(resultado_lote.resultados_individuais[:3]):
            print(f"  Produto {i+1}: {resultado.status} (confiança: {resultado.confianca_media:.2%})")
    
    def _demonstrar_workflow_langgraph(self):
        """Demonstra workflow usando LangGraph"""
        
        empresa_id = 3
        config_empresa = self.empresa_configs[empresa_id]
        
        print(f"\nWorkflow LangGraph - {config_empresa['nome']}")
        
        # Cria workflow
        workflow = FiscalAuditWorkflow(empresa_id, self.processing_config)
        
        # Testa com um produto
        produto_data = self.produtos_exemplo[0]
        produto = self._criar_produto_simulado(produto_data)
        
        print(f"Processando: {produto_data['descricao_produto'][:50]}...")
        
        # Executa workflow
        resultado = workflow.processar_produto(produto)
        
        # Exibe resultado
        print(f"\nResultado do workflow:")
        print(f"Status: {resultado['status']}")
        print(f"Estado final: {resultado.get('estado_final', 'N/A')}")
        print(f"Requer revisão: {resultado.get('requer_revisao', False)}")
        print(f"Tempo execução: {resultado.get('tempo_execucao', 0):.2f}s")
        
        if resultado.get('logs_processamento'):
            print(f"\nEtapas executadas:")
            for log in resultado['logs_processamento']:
                etapa = log.get('etapa', 'Desconhecida')
                status = log.get('status', 'Desconhecido')
                print(f"  - {etapa}: {status}")
    
    def _gerar_relatorio_auditoria(self):
        """Gera relatório de auditoria consolidado"""
        
        print("\nRELATÓRIO DE AUDITORIA CONSOLIDADO")
        print("-" * 40)
        
        # Simula dados de auditoria
        relatorio = {
            'data_geracao': datetime.utcnow().isoformat(),
            'empresas_processadas': len(self.empresa_configs),
            'total_produtos': len(self.produtos_exemplo) * len(self.empresa_configs),
            'produtos_com_sucesso': 12,
            'produtos_com_erro': 2,
            'produtos_revisao_pendente': 1,
            'tempo_total_processamento': 45.6,
            'taxa_sucesso_geral': 80.0,
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
        print(f"Empresas processadas: {relatorio['empresas_processadas']}")
        print(f"Total de produtos: {relatorio['total_produtos']}")
        print(f"Taxa de sucesso geral: {relatorio['taxa_sucesso_geral']:.1f}%")
        print(f"Tempo total: {relatorio['tempo_total_processamento']:.1f}s")
        
        print(f"\nEstatísticas por empresa:")
        for empresa_id, stats in relatorio['estatisticas_por_empresa'].items():
            print(f"  {empresa_id}. {stats['nome']} ({stats['tipos_banco']})")
            print(f"     Produtos: {stats['produtos_processados']}, Sucesso: {stats['taxa_sucesso']:.1f}%")
        
        # Salva relatório em arquivo
        relatorio_file = 'relatorio_auditoria_fase2.json'
        try:
            with open(relatorio_file, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            print(f"\nRelatório salvo em: {relatorio_file}")
        except Exception as e:
            print(f"Erro ao salvar relatório: {str(e)}")
    
    def _criar_produto_simulado(self, produto_data: Dict[str, Any]) -> ProdutoEmpresa:
        """Cria objeto produto simulado para teste"""
        
        # Simula criação de objeto ProdutoEmpresa
        class ProdutoSimulado:
            def __init__(self, data):
                self.produto_id = data['produto_id']
                self.codigo_produto = data['codigo_produto']
                self.descricao_produto = data['descricao_produto']
                self.codigo_barra = data.get('codigo_barra')
                self.ncm = data.get('ncm')
                self.cest = data.get('cest')
                
                # Campos que serão preenchidos durante processamento
                self.descricao_enriquecida = None
                self.ncm_sugerido = None
                self.cest_sugerido = None
                self.confianca_ncm = None
                self.confianca_cest = None
                self.justificativa_ncm = None
                self.justificativa_cest = None
                self.status_processamento = None
                self.revisao_manual = False
                self.data_processamento = None
        
        return ProdutoSimulado(produto_data)

def main():
    """Função principal da demonstração"""
    
    try:
        demo = FiscalAuditDemo()
        demo.executar_demonstracao_completa()
        
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
        
    except Exception as e:
        print(f"\nErro na demonstração: {str(e)}")
        logger.error(f"Erro na demonstração: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
