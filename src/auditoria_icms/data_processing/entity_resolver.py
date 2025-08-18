"""
Entity Resolution para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pela resolução e deduplicação de entidades na base de conhecimento
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
import logging
from datetime import datetime
from collections import defaultdict
import difflib
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EntityResolver:
    """Classe para resolução e deduplicação de entidades"""
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 similarity_threshold: float = 0.85,
                 data_dir: str = None):
        
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "auditoria123")
        self.similarity_threshold = similarity_threshold
        self.data_dir = data_dir or "./data/raw"
        
        # Inicializa driver Neo4j
        self.driver = self._initialize_neo4j()
        
        # Estatísticas de resolução
        self.resolution_stats = {
            'entities_processed': 0,
            'duplicates_found': 0,
            'duplicates_merged': 0,
            'conflicts_resolved': 0,
            'new_entities_created': 0,
            'errors': 0
        }
        
        # Padrões para normalização
        self.normalization_patterns = {
            'ncm_code': re.compile(r'[^0-9]'),
            'cest_code': re.compile(r'[^0-9.]'),
            'gtin_code': re.compile(r'[^0-9]'),
            'description_cleanup': re.compile(r'\s+'),
            'special_chars': re.compile(r'[^\w\s-]')
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
                result = session.run("RETURN 'Entity Resolver conectado!' as message")
                message = result.single()["message"]
                logger.info(message)
            
            return driver
            
        except ImportError:
            logger.warning("neo4j driver não disponível, usando simulação")
            return None
        except Exception as e:
            logger.error(f"Erro ao conectar com Neo4j: {e}")
            return None
    
    def normalize_text(self, text: str, entity_type: str = "general") -> str:
        """Normaliza texto baseado no tipo de entidade."""
        if not text:
            return ""
        
        text = text.strip().upper()
        
        if entity_type == "ncm_code":
            return self.normalization_patterns['ncm_code'].sub('', text)
        elif entity_type == "cest_code":
            return self.normalization_patterns['cest_code'].sub('', text)
        elif entity_type == "gtin_code":
            return self.normalization_patterns['gtin_code'].sub('', text)
        elif entity_type == "description":
            # Remove caracteres especiais e normaliza espaços
            text = self.normalization_patterns['special_chars'].sub('', text)
            text = self.normalization_patterns['description_cleanup'].sub(' ', text)
            return text.strip()
        else:
            return text
    
    def calculate_similarity(self, text1: str, text2: str, method: str = "ratio") -> float:
        """Calcula similaridade entre dois textos."""
        if not text1 or not text2:
            return 0.0
        
        text1_norm = self.normalize_text(text1, "description")
        text2_norm = self.normalize_text(text2, "description")
        
        if method == "ratio":
            return difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
        elif method == "quick_ratio":
            return difflib.SequenceMatcher(None, text1_norm, text2_norm).quick_ratio()
        elif method == "real_quick_ratio":
            return difflib.SequenceMatcher(None, text1_norm, text2_norm).real_quick_ratio()
        else:
            return difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    def find_ncm_duplicates(self) -> List[Dict]:
        """Encontra possíveis duplicatas de NCM."""
        logger.info("Procurando duplicatas de NCM...")
        
        duplicates = []
        
        if self.driver is None:
            # Simulação para demonstração
            simulated_duplicates = [
                {
                    "nodes": [
                        {"codigo": "30049069", "descricao": "Outros medicamentos constituídos por produtos misturados"},
                        {"codigo": "30049069", "descricao": "OUTROS MEDICAMENTOS CONSTITUIDOS POR PRODUTOS MISTURADOS"}
                    ],
                    "similarity": 0.92,
                    "conflict_type": "description_variation"
                }
            ]
            logger.info("Simulando busca de duplicatas NCM")
            return simulated_duplicates
        
        try:
            with self.driver.session() as session:
                # Busca NCMs com códigos similares ou descrições similares
                query = """
                MATCH (n1:NCM), (n2:NCM)
                WHERE n1.codigo = n2.codigo AND elementId(n1) < elementId(n2)
                OR (
                    n1.codigo <> n2.codigo AND
                    apoc.text.levenshteinSimilarity(n1.descricao, n2.descricao) > $threshold
                )
                RETURN n1, n2
                """
                
                result = session.run(query, threshold=self.similarity_threshold)
                
                for record in result:
                    n1 = record["n1"]
                    n2 = record["n2"]
                    
                    similarity = self.calculate_similarity(n1["descricao"], n2["descricao"])
                    
                    if similarity >= self.similarity_threshold:
                        duplicates.append({
                            "nodes": [dict(n1), dict(n2)],
                            "similarity": similarity,
                            "conflict_type": "same_code" if n1["codigo"] == n2["codigo"] else "similar_description"
                        })
                
        except Exception as e:
            logger.error(f"Erro ao buscar duplicatas NCM: {e}")
            self.resolution_stats['errors'] += 1
        
        logger.info(f"Encontradas {len(duplicates)} possíveis duplicatas de NCM")
        return duplicates
    
    def find_product_duplicates(self) -> List[Dict]:
        """Encontra possíveis duplicatas de produtos."""
        logger.info("Procurando duplicatas de produtos...")
        
        duplicates = []
        
        if self.driver is None:
            # Simulação
            simulated_duplicates = [
                {
                    "nodes": [
                        {"gtin": "7891234567890", "descricao": "DIPIRONA SODICA 500MG", "marca": "Medley"},
                        {"gtin": "7891234567899", "descricao": "DIPIRONA SÓDICA 500MG", "marca": "MEDLEY"}
                    ],
                    "similarity": 0.95,
                    "conflict_type": "similar_description"
                }
            ]
            logger.info("Simulando busca de duplicatas de produtos")
            return simulated_duplicates
        
        try:
            with self.driver.session() as session:
                # Busca produtos com descrições similares
                query = """
                MATCH (p1:Produto), (p2:Produto)
                WHERE p1.gtin <> p2.gtin AND elementId(p1) < elementId(p2)
                AND (
                    apoc.text.levenshteinSimilarity(p1.descricao, p2.descricao) > $threshold
                    OR (p1.marca = p2.marca AND 
                        apoc.text.levenshteinSimilarity(p1.descricao, p2.descricao) > $lower_threshold)
                )
                RETURN p1, p2
                """
                
                result = session.run(query, 
                                   threshold=self.similarity_threshold,
                                   lower_threshold=self.similarity_threshold - 0.1)
                
                for record in result:
                    p1 = record["p1"]
                    p2 = record["p2"]
                    
                    similarity = self.calculate_similarity(p1["descricao"], p2["descricao"])
                    
                    if similarity >= self.similarity_threshold - 0.1:  # Threshold mais baixo para produtos
                        duplicates.append({
                            "nodes": [dict(p1), dict(p2)],
                            "similarity": similarity,
                            "conflict_type": "similar_description"
                        })
                
        except Exception as e:
            logger.error(f"Erro ao buscar duplicatas de produtos: {e}")
            self.resolution_stats['errors'] += 1
        
        logger.info(f"Encontradas {len(duplicates)} possíveis duplicatas de produtos")
        return duplicates
    
    def resolve_ncm_conflicts(self, duplicates: List[Dict]) -> List[Dict]:
        """Resolve conflitos de NCM."""
        logger.info("Resolvendo conflitos de NCM...")
        
        resolutions = []
        
        for duplicate in duplicates:
            nodes = duplicate["nodes"]
            conflict_type = duplicate["conflict_type"]
            
            if conflict_type == "same_code":
                # Mesmo código NCM, manter descrição mais completa
                n1, n2 = nodes[0], nodes[1]
                
                if len(n1["descricao"]) >= len(n2["descricao"]):
                    master_node = n1
                    duplicate_node = n2
                else:
                    master_node = n2
                    duplicate_node = n1
                
                resolution = {
                    "action": "merge",
                    "master_node": master_node,
                    "duplicate_node": duplicate_node,
                    "reason": "same_code_longer_description"
                }
                
                if self.driver:
                    self._merge_ncm_nodes(master_node, duplicate_node)
                
                resolutions.append(resolution)
                self.resolution_stats['duplicates_merged'] += 1
                
            elif conflict_type == "similar_description":
                # Descrições similares, códigos diferentes - manter ambos mas marcar relacionamento
                resolution = {
                    "action": "link_similar",
                    "nodes": nodes,
                    "reason": "similar_descriptions_different_codes"
                }
                
                if self.driver:
                    self._link_similar_ncm_nodes(nodes[0], nodes[1])
                
                resolutions.append(resolution)
                self.resolution_stats['conflicts_resolved'] += 1
        
        logger.info(f"Resolvidos {len(resolutions)} conflitos de NCM")
        return resolutions
    
    def resolve_product_conflicts(self, duplicates: List[Dict]) -> List[Dict]:
        """Resolve conflitos de produtos."""
        logger.info("Resolvendo conflitos de produtos...")
        
        resolutions = []
        
        for duplicate in duplicates:
            nodes = duplicate["nodes"]
            p1, p2 = nodes[0], nodes[1]
            
            # Para produtos, manter ambos mas criar relacionamento de similaridade
            resolution = {
                "action": "link_similar",
                "nodes": nodes,
                "reason": "similar_products_different_gtins"
            }
            
            if self.driver:
                self._link_similar_product_nodes(p1, p2)
            
            resolutions.append(resolution)
            self.resolution_stats['conflicts_resolved'] += 1
        
        logger.info(f"Resolvidos {len(resolutions)} conflitos de produtos")
        return resolutions
    
    def _merge_ncm_nodes(self, master_node: Dict, duplicate_node: Dict):
        """Merge dois nós NCM."""
        if self.driver is None:
            return
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (master:NCM {codigo: $master_codigo})
                MATCH (duplicate:NCM {codigo: $duplicate_codigo})
                WHERE elementId(master) <> elementId(duplicate)
                
                // Transfere relacionamentos do duplicado para o master
                MATCH (duplicate)-[r]-(other)
                WHERE NOT (master)-[]-(other)
                WITH master, duplicate, other, type(r) as rel_type, properties(r) as rel_props
                CALL apoc.create.relationship(master, rel_type, rel_props, other) YIELD rel
                
                // Remove o nó duplicado
                WITH duplicate
                DETACH DELETE duplicate
                """
                
                session.run(query, 
                           master_codigo=master_node["codigo"],
                           duplicate_codigo=duplicate_node["codigo"])
                
        except Exception as e:
            logger.error(f"Erro ao fazer merge de NCM: {e}")
    
    def _link_similar_ncm_nodes(self, node1: Dict, node2: Dict):
        """Cria relacionamento de similaridade entre NCMs."""
        if self.driver is None:
            return
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n1:NCM {codigo: $codigo1})
                MATCH (n2:NCM {codigo: $codigo2})
                MERGE (n1)-[:SIMILAR_TO {similarity: $similarity, created: datetime()}]-(n2)
                """
                
                similarity = self.calculate_similarity(node1["descricao"], node2["descricao"])
                
                session.run(query, 
                           codigo1=node1["codigo"],
                           codigo2=node2["codigo"],
                           similarity=similarity)
                
        except Exception as e:
            logger.error(f"Erro ao linkar NCMs similares: {e}")
    
    def _link_similar_product_nodes(self, node1: Dict, node2: Dict):
        """Cria relacionamento de similaridade entre produtos."""
        if self.driver is None:
            return
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p1:Produto {gtin: $gtin1})
                MATCH (p2:Produto {gtin: $gtin2})
                MERGE (p1)-[:SIMILAR_TO {similarity: $similarity, created: datetime()}]-(p2)
                """
                
                similarity = self.calculate_similarity(node1["descricao"], node2["descricao"])
                
                session.run(query, 
                           gtin1=node1["gtin"],
                           gtin2=node2["gtin"],
                           similarity=similarity)
                
        except Exception as e:
            logger.error(f"Erro ao linkar produtos similares: {e}")
    
    def validate_entity_integrity(self) -> Dict:
        """Valida integridade das entidades no grafo."""
        logger.info("Validando integridade das entidades...")
        
        validation_results = {
            "orphaned_nodes": 0,
            "missing_properties": 0,
            "invalid_codes": 0,
            "circular_references": 0,
            "validation_errors": []
        }
        
        if self.driver is None:
            logger.info("Simulando validação de integridade")
            validation_results["orphaned_nodes"] = 2
            validation_results["missing_properties"] = 1
            return validation_results
        
        try:
            with self.driver.session() as session:
                # Busca nós órfãos (sem relacionamentos)
                orphaned_query = "MATCH (n) WHERE NOT (n)-[]-() RETURN count(n) as count"
                result = session.run(orphaned_query)
                validation_results["orphaned_nodes"] = result.single()["count"]
                
                # Busca nós com propriedades obrigatórias faltando
                missing_props_queries = [
                    "MATCH (n:NCM) WHERE n.codigo IS NULL OR n.descricao IS NULL RETURN count(n) as count",
                    "MATCH (p:Produto) WHERE p.gtin IS NULL OR p.descricao IS NULL RETURN count(p) as count",
                    "MATCH (c:CEST) WHERE c.id IS NULL OR c.descricao IS NULL RETURN count(c) as count"
                ]
                
                total_missing = 0
                for query in missing_props_queries:
                    result = session.run(query)
                    total_missing += result.single()["count"]
                
                validation_results["missing_properties"] = total_missing
                
                # Valida formatos de códigos
                invalid_codes_query = """
                MATCH (n:NCM) 
                WHERE NOT n.codigo =~ '^[0-9]{8}$'
                RETURN count(n) as count
                """
                result = session.run(invalid_codes_query)
                validation_results["invalid_codes"] = result.single()["count"]
                
        except Exception as e:
            logger.error(f"Erro na validação de integridade: {e}")
            validation_results["validation_errors"].append(str(e))
        
        logger.info(f"Validação concluída: {validation_results}")
        return validation_results
    
    def generate_entity_resolution_report(self) -> Dict:
        """Gera relatório completo da resolução de entidades."""
        logger.info("Gerando relatório de resolução de entidades...")
        
        # Encontra duplicatas
        ncm_duplicates = self.find_ncm_duplicates()
        product_duplicates = self.find_product_duplicates()
        
        # Resolve conflitos
        ncm_resolutions = self.resolve_ncm_conflicts(ncm_duplicates)
        product_resolutions = self.resolve_product_conflicts(product_duplicates)
        
        # Valida integridade
        integrity_validation = self.validate_entity_integrity()
        
        # Compila relatório
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "ncm_duplicates_found": len(ncm_duplicates),
                "product_duplicates_found": len(product_duplicates),
                "ncm_conflicts_resolved": len(ncm_resolutions),
                "product_conflicts_resolved": len(product_resolutions),
                "total_entities_processed": self.resolution_stats['entities_processed'],
                "duplicates_merged": self.resolution_stats['duplicates_merged'],
                "conflicts_resolved": self.resolution_stats['conflicts_resolved']
            },
            "duplicates": {
                "ncm": ncm_duplicates,
                "products": product_duplicates
            },
            "resolutions": {
                "ncm": ncm_resolutions,
                "products": product_resolutions
            },
            "integrity_validation": integrity_validation,
            "statistics": self.resolution_stats
        }
        
        return report
    
    def save_resolution_report(self, report: Dict):
        """Salva relatório de resolução."""
        report_file = "./data/processed/entity_resolution_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Relatório de resolução salvo: {report_file}")
    
    def run_entity_resolution(self):
        """Executa o processo completo de resolução de entidades."""
        logger.info("=== Iniciando Resolução de Entidades ===")
        
        # Gera relatório completo
        report = self.generate_entity_resolution_report()
        
        # Salva relatório
        self.save_resolution_report(report)
        
        logger.info("=== Resolução de Entidades Concluída ===")
        logger.info(f"Resumo: {report['summary']}")
        
        return report
    
    def close(self):
        """Fecha conexão com Neo4j."""
        if self.driver:
            self.driver.close()
            logger.info("Conexão Neo4j fechada")

def main():
    """Função principal para teste."""
    resolver = EntityResolver()
    
    try:
        report = resolver.run_entity_resolution()
        logger.info(f"Resolução concluída: {report['summary']}")
    finally:
        resolver.close()

if __name__ == "__main__":
    main()
