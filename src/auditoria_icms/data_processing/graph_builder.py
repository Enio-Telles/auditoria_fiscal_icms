"""
Graph Builder para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pela criação do grafo de conhecimento NCM-CEST em Neo4j
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphBuilder:
    """Classe para construção do grafo de conhecimento fiscal"""
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 data_dir: str = None):
        
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "auditoria123")
        self.data_dir = data_dir or "./data/raw"
        
        # Inicializa driver Neo4j
        self.driver = self._initialize_neo4j()
        
        # Contadores para estatísticas
        self.stats = {
            'nodes_created': 0,
            'relationships_created': 0,
            'capitulos': 0,
            'posicoes': 0,
            'subposicoes': 0,
            'subitems': 0,
            'cest_rules': 0,
            'segmentos': 0,
            'produtos': 0
        }
    
    def _initialize_neo4j(self):
        """Inicializa conexão com Neo4j."""
        try:
            from neo4j import GraphDatabase
            logger.info(f"Conectando ao Neo4j: {self.neo4j_uri}")
            driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Testa conexão
            with driver.session() as session:
                result = session.run("RETURN 'Neo4j conectado!' as message")
                message = result.single()["message"]
                logger.info(message)
            
            return driver
            
        except ImportError:
            logger.warning("neo4j driver não disponível, usando simulação")
            return None
        except Exception as e:
            logger.error(f"Erro ao conectar com Neo4j: {e}")
            return None
    
    def clear_database(self):
        """Limpa o banco de dados Neo4j."""
        if self.driver is None:
            logger.info("Simulando limpeza do banco de dados")
            return
        
        logger.info("Limpando banco de dados Neo4j...")
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Banco de dados limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar banco: {e}")
    
    def create_indexes(self):
        """Cria índices para performance."""
        if self.driver is None:
            logger.info("Simulando criação de índices")
            return
        
        logger.info("Criando índices...")
        
        indexes = [
            "CREATE INDEX ncm_codigo_idx IF NOT EXISTS FOR (n:NCM) ON (n.codigo)",
            "CREATE INDEX capitulo_id_idx IF NOT EXISTS FOR (c:Capitulo) ON (c.id)",
            "CREATE INDEX posicao_id_idx IF NOT EXISTS FOR (p:Posicao) ON (p.id)",
            "CREATE INDEX subposicao_id_idx IF NOT EXISTS FOR (s:Subposicao) ON (s.id)",
            "CREATE INDEX cest_id_idx IF NOT EXISTS FOR (c:CEST) ON (c.id)",
            "CREATE INDEX segmento_id_idx IF NOT EXISTS FOR (s:Segmento) ON (s.id)",
            "CREATE INDEX produto_gtin_idx IF NOT EXISTS FOR (p:Produto) ON (p.gtin)"
        ]
        
        try:
            with self.driver.session() as session:
                for index_query in indexes:
                    session.run(index_query)
            logger.info("Índices criados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar índices: {e}")
    
    def create_ncm_hierarchy_nodes(self) -> Dict[str, int]:
        """Cria nós da hierarquia NCM."""
        logger.info("Criando hierarquia NCM...")
        
        # Dados NCM simulados para teste inicial
        ncm_data = [
            {"codigo": "30049069", "descricao": "Outros medicamentos constituídos por produtos misturados ou não misturados"},
            {"codigo": "85171211", "descricao": "Telefones móveis e de outras redes sem fio"},
            {"codigo": "22021000", "descricao": "Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar"},
            {"codigo": "85171212", "descricao": "Telefones inteligentes"},
            {"codigo": "30049070", "descricao": "Medicamentos homeopáticos"},
        ]
        
        nodes_created = 0
        
        # Agrupa por hierarquia
        capitulos = set()
        posicoes = set()
        subposicoes = set()
        subitems = set()
        
        for item in ncm_data:
            codigo = item["codigo"]
            capitulo = codigo[:2]
            posicao = codigo[:4]
            subposicao = codigo[:6]
            
            capitulos.add(capitulo)
            posicoes.add(posicao)
            subposicoes.add(subposicao)
            subitems.add(codigo)
        
        if self.driver:
            with self.driver.session() as session:
                # Cria capítulos
                for cap in capitulos:
                    query = """
                    MERGE (c:Capitulo {id: $cap})
                    ON CREATE SET c.created = datetime()
                    """
                    session.run(query, cap=cap)
                    nodes_created += 1
                
                # Cria posições
                for pos in posicoes:
                    cap = pos[:2]
                    query = """
                    MERGE (p:Posicao {id: $pos})
                    ON CREATE SET p.created = datetime()
                    WITH p
                    MATCH (c:Capitulo {id: $cap})
                    MERGE (p)-[:PERTENCE_A]->(c)
                    """
                    session.run(query, pos=pos, cap=cap)
                    nodes_created += 1
                
                # Cria subposições
                for sub in subposicoes:
                    pos = sub[:4]
                    query = """
                    MERGE (s:Subposicao {id: $sub})
                    ON CREATE SET s.created = datetime()
                    WITH s
                    MATCH (p:Posicao {id: $pos})
                    MERGE (s)-[:PERTENCE_A]->(p)
                    """
                    session.run(query, sub=sub, pos=pos)
                    nodes_created += 1
                
                # Cria subitens (NCM completos)
                for item in ncm_data:
                    codigo = item["codigo"]
                    descricao = item["descricao"]
                    sub = codigo[:6]
                    
                    query = """
                    MERGE (n:NCM {codigo: $codigo})
                    ON CREATE SET 
                        n.descricao = $descricao,
                        n.created = datetime()
                    WITH n
                    MATCH (s:Subposicao {id: $sub})
                    MERGE (n)-[:PERTENCE_A]->(s)
                    """
                    session.run(query, codigo=codigo, descricao=descricao, sub=sub)
                    nodes_created += 1
        else:
            # Simulação
            nodes_created = len(capitulos) + len(posicoes) + len(subposicoes) + len(subitems)
            logger.info("Simulando criação de hierarquia NCM")
        
        self.stats['capitulos'] = len(capitulos)
        self.stats['posicoes'] = len(posicoes)
        self.stats['subposicoes'] = len(subposicoes)
        self.stats['subitems'] = len(subitems)
        self.stats['nodes_created'] += nodes_created
        
        logger.info(f"Hierarquia NCM criada: {nodes_created} nós")
        return {"nodes_created": nodes_created}
    
    def create_cest_nodes(self) -> Dict[str, int]:
        """Cria nós CEST e segmentos."""
        logger.info("Criando nós CEST...")
        
        # Dados CEST simulados
        cest_data = [
            {"cest": "17.004.00", "descricao": "Medicamentos genéricos", "segmento_id": 1, "segmento_desc": "Medicamentos"},
            {"cest": "21.001.00", "descricao": "Aparelhos telefônicos", "segmento_id": 2, "segmento_desc": "Telecomunicações"},
            {"cest": "28.064.00", "descricao": "Artigos de vestuário infantil", "segmento_id": 3, "segmento_desc": "Vestuário"},
        ]
        
        segmentos_data = [
            {"id": 1, "descricao": "Medicamentos"},
            {"id": 2, "descricao": "Telecomunicações"},
            {"id": 3, "descricao": "Vestuário"},
        ]
        
        nodes_created = 0
        
        if self.driver:
            with self.driver.session() as session:
                # Cria segmentos
                for seg in segmentos_data:
                    query = """
                    MERGE (s:Segmento {id: $seg_id})
                    ON CREATE SET 
                        s.descricao = $descricao,
                        s.created = datetime()
                    """
                    session.run(query, seg_id=seg["id"], descricao=seg["descricao"])
                    nodes_created += 1
                
                # Cria regras CEST
                for cest in cest_data:
                    query = """
                    MERGE (c:CEST {id: $cest_id})
                    ON CREATE SET 
                        c.descricao = $descricao,
                        c.created = datetime()
                    WITH c
                    MATCH (s:Segmento {id: $seg_id})
                    MERGE (c)-[:CONTIDO_EM]->(s)
                    """
                    session.run(query, 
                                cest_id=cest["cest"], 
                                descricao=cest["descricao"],
                                seg_id=cest["segmento_id"])
                    nodes_created += 1
        else:
            # Simulação
            nodes_created = len(segmentos_data) + len(cest_data)
            logger.info("Simulando criação de nós CEST")
        
        self.stats['segmentos'] = len(segmentos_data)
        self.stats['cest_rules'] = len(cest_data)
        self.stats['nodes_created'] += nodes_created
        
        logger.info(f"Nós CEST criados: {nodes_created}")
        return {"nodes_created": nodes_created}
    
    def create_ncm_cest_relationships(self) -> Dict[str, int]:
        """Cria relacionamentos NCM-CEST."""
        logger.info("Criando relacionamentos NCM-CEST...")
        
        # Associações NCM-CEST simuladas
        associations = [
            {"cest": "17.004.00", "ncm_pattern": "30*", "tipo": "padrao", "nivel": "capitulo"},
            {"cest": "21.001.00", "ncm_pattern": "85171211", "tipo": "especifico", "nivel": "subitem"},
            {"cest": "21.001.00", "ncm_pattern": "85171212", "tipo": "especifico", "nivel": "subitem"},
        ]
        
        relationships_created = 0
        
        if self.driver:
            with self.driver.session() as session:
                for assoc in associations:
                    cest_id = assoc["cest"]
                    pattern = assoc["ncm_pattern"]
                    tipo = assoc["tipo"]
                    nivel = assoc["nivel"]
                    
                    if tipo == "especifico":
                        # Relacionamento direto com NCM específico
                        query = """
                        MATCH (c:CEST {id: $cest_id})
                        MATCH (n:NCM {codigo: $pattern})
                        MERGE (n)-[:TEM_REGRA_CEST {tipo: $tipo, nivel: $nivel}]->(c)
                        """
                        session.run(query, cest_id=cest_id, pattern=pattern, tipo=tipo, nivel=nivel)
                        relationships_created += 1
                    
                    elif tipo == "padrao":
                        # Relacionamento hierárquico
                        if nivel == "capitulo":
                            cap_id = pattern.replace("*", "")
                            query = """
                            MATCH (c:CEST {id: $cest_id})
                            MATCH (cap:Capitulo {id: $cap_id})
                            MERGE (cap)-[:TEM_REGRA_CEST {tipo: $tipo, nivel: $nivel, pattern: $pattern}]->(c)
                            """
                            session.run(query, cest_id=cest_id, cap_id=cap_id, tipo=tipo, nivel=nivel, pattern=pattern)
                            relationships_created += 1
        else:
            # Simulação
            relationships_created = len(associations)
            logger.info("Simulando criação de relacionamentos NCM-CEST")
        
        self.stats['relationships_created'] += relationships_created
        
        logger.info(f"Relacionamentos NCM-CEST criados: {relationships_created}")
        return {"relationships_created": relationships_created}
    
    def create_product_nodes(self) -> Dict[str, int]:
        """Cria nós de produtos exemplo."""
        logger.info("Criando nós de produtos...")
        
        # Produtos exemplo simulados
        products = [
            {"gtin": "7891234567890", "descricao": "DIPIRONA SODICA 500MG", "ncm": "30049069", "marca": "Medley"},
            {"gtin": "7891234567891", "descricao": "SMARTPHONE GALAXY A54", "ncm": "85171211", "marca": "Samsung"},
            {"gtin": "7891234567892", "descricao": "COCA-COLA 350ML", "ncm": "22021000", "marca": "Coca-Cola"},
        ]
        
        nodes_created = 0
        
        if self.driver:
            with self.driver.session() as session:
                for product in products:
                    # Cria produto
                    query = """
                    MERGE (p:Produto {gtin: $gtin})
                    ON CREATE SET 
                        p.descricao = $descricao,
                        p.marca = $marca,
                        p.created = datetime()
                    """
                    session.run(query, 
                                gtin=product["gtin"],
                                descricao=product["descricao"],
                                marca=product["marca"])
                    nodes_created += 1
                    
                    # Liga produto ao NCM
                    if product["ncm"]:
                        query = """
                        MATCH (p:Produto {gtin: $gtin})
                        MATCH (n:NCM {codigo: $ncm})
                        MERGE (p)-[:EXEMPLO_DE]->(n)
                        """
                        session.run(query, gtin=product["gtin"], ncm=product["ncm"])
                        self.stats['relationships_created'] += 1
        else:
            # Simulação
            nodes_created = len(products)
            logger.info("Simulando criação de produtos")
        
        self.stats['produtos'] = len(products)
        self.stats['nodes_created'] += nodes_created
        
        logger.info(f"Produtos criados: {nodes_created}")
        return {"nodes_created": nodes_created}
    
    def run_example_queries(self):
        """Executa queries de exemplo para testar o grafo."""
        logger.info("Executando queries de exemplo...")
        
        if self.driver is None:
            logger.info("Simulando execução de queries")
            return
        
        queries = [
            {
                "name": "NCMs do Capítulo 30 (Medicamentos)",
                "query": """
                MATCH (cap:Capitulo {id: '30'})<-[:PERTENCE_A*]-(n:NCM)
                RETURN n.codigo, n.descricao
                LIMIT 5
                """
            },
            {
                "name": "Regras CEST aplicáveis ao Capítulo 30",
                "query": """
                MATCH (cap:Capitulo {id: '30'})-[:TEM_REGRA_CEST]->(cest:CEST)
                RETURN cest.id, cest.descricao
                """
            },
            {
                "name": "Produtos com seus NCMs",
                "query": """
                MATCH (p:Produto)-[:EXEMPLO_DE]->(n:NCM)
                RETURN p.descricao, n.codigo, n.descricao
                LIMIT 5
                """
            },
            {
                "name": "Hierarquia completa de um NCM",
                "query": """
                MATCH path = (n:NCM {codigo: '30049069'})-[:PERTENCE_A*]->(cap:Capitulo)
                RETURN path
                """
            }
        ]
        
        try:
            with self.driver.session() as session:
                for query_info in queries:
                    logger.info(f"Executando: {query_info['name']}")
                    result = session.run(query_info["query"])
                    records = list(result)
                    logger.info(f"Resultado: {len(records)} registros encontrados")
                    
                    if records:
                        for i, record in enumerate(records[:2]):  # Mostra apenas os 2 primeiros
                            logger.info(f"  {i+1}: {dict(record)}")
                    
        except Exception as e:
            logger.error(f"Erro ao executar queries: {e}")
    
    def generate_graph_statistics(self) -> Dict:
        """Gera estatísticas do grafo criado."""
        logger.info("Gerando estatísticas do grafo...")
        
        if self.driver is None:
            return self.stats
        
        try:
            with self.driver.session() as session:
                # Conta nós por tipo
                node_counts = {}
                labels = ["Capitulo", "Posicao", "Subposicao", "NCM", "CEST", "Segmento", "Produto"]
                
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count = result.single()["count"]
                    node_counts[label.lower()] = count
                
                # Conta relacionamentos por tipo
                rel_counts = {}
                rel_types = ["PERTENCE_A", "TEM_REGRA_CEST", "CONTIDO_EM", "EXEMPLO_DE"]
                
                for rel_type in rel_types:
                    result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    count = result.single()["count"]
                    rel_counts[rel_type.lower()] = count
                
                # Total geral
                total_nodes_result = session.run("MATCH (n) RETURN count(n) as count")
                total_nodes = total_nodes_result.single()["count"]
                
                total_rels_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                total_rels = total_rels_result.single()["count"]
                
                stats = {
                    "total_nodes": total_nodes,
                    "total_relationships": total_rels,
                    "nodes_by_type": node_counts,
                    "relationships_by_type": rel_counts,
                    "created_at": datetime.now().isoformat()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return self.stats
    
    def save_graph_metadata(self, stats: Dict):
        """Salva metadados do grafo criado."""
        metadata_file = "./data/processed/graph_metadata.json"
        os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadados do grafo salvos: {metadata_file}")
    
    def build_complete_graph(self):
        """Constrói o grafo completo de conhecimento."""
        logger.info("=== Construção do Grafo de Conhecimento ===")
        
        # Limpa banco
        self.clear_database()
        
        # Cria índices
        self.create_indexes()
        
        # Cria estruturas
        self.create_ncm_hierarchy_nodes()
        self.create_cest_nodes()
        self.create_ncm_cest_relationships()
        self.create_product_nodes()
        
        # Testa com queries
        self.run_example_queries()
        
        # Gera estatísticas
        final_stats = self.generate_graph_statistics()
        
        # Salva metadados
        self.save_graph_metadata(final_stats)
        
        logger.info("=== Construção do Grafo Concluída ===")
        logger.info(f"Estatísticas finais: {final_stats}")
        
        return final_stats
    
    def close(self):
        """Fecha conexão com Neo4j."""
        if self.driver:
            self.driver.close()
            logger.info("Conexão Neo4j fechada")

def main():
    """Função principal para teste."""
    builder = GraphBuilder()
    
    try:
        stats = builder.build_complete_graph()
        logger.info(f"Grafo construído com sucesso: {stats}")
    finally:
        builder.close()

if __name__ == "__main__":
    main()
