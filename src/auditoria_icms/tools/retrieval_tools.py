"""
Ferramentas de Busca e Recuperação - Retrieval Tools
Implementa as ferramentas de busca na base de conhecimento tri-híbrida.
"""

import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging


class RetrievalTools:
    """
    Ferramentas de busca e recuperação para a base de conhecimento.
    Integra busca relacional (SQLite), vetorial (FAISS) e em grafo (Neo4j).
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Configurações dos bancos
        self.sqlite_path = config.get("relational_store", {}).get(
            "database_path", "data/processed/knowledge_base.sqlite"
        )
        self.faiss_index_path = config.get("vector_store", {}).get(
            "index_path", "data/processed/faiss_index"
        )
        self.neo4j_config = config.get("graph_store", {})

        # Componentes de busca
        self.sqlite_conn = None
        self.faiss_index = None
        self.neo4j_driver = None
        self.embeddings_model = None

        # Cache de busca
        self._cache = {}
        self._cache_size_limit = 1000

    async def initialize(self):
        """Inicializa todas as conexões e modelos."""
        try:
            # Inicializar SQLite
            await self._init_sqlite()

            # Inicializar embeddings
            await self._init_embeddings()

            # Inicializar FAISS (se disponível)
            await self._init_faiss()

            # Inicializar Neo4j (se disponível)
            await self._init_neo4j()

            self.logger.info("RetrievalTools inicializado com sucesso")

        except Exception as e:
            self.logger.error(f"Erro na inicialização: {str(e)}")
            raise

    async def _init_sqlite(self):
        """Inicializa conexão SQLite."""
        if Path(self.sqlite_path).exists():
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            self.logger.info("Conexão SQLite estabelecida")
        else:
            self.logger.warning(f"Base SQLite não encontrada em {self.sqlite_path}")

    async def _init_embeddings(self):
        """Inicializa modelo de embeddings."""
        try:
            # Importação condicional para evitar erro se não instalado
            from sentence_transformers import SentenceTransformer

            model_name = self.config.get("embeddings", {}).get(
                "model_name", "BAAI/bge-m3"
            )
            self.embeddings_model = SentenceTransformer(model_name)
            self.logger.info(f"Modelo de embeddings carregado: {model_name}")

        except ImportError:
            self.logger.warning(
                "sentence-transformers não disponível - busca semântica desabilitada"
            )
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo de embeddings: {str(e)}")

    async def _init_faiss(self):
        """Inicializa índice FAISS."""
        try:
            import faiss

            index_file = f"{self.faiss_index_path}/index.faiss"
            if Path(index_file).exists():
                self.faiss_index = faiss.read_index(index_file)
                self.logger.info("Índice FAISS carregado")
            else:
                self.logger.warning("Índice FAISS não encontrado")

        except ImportError:
            self.logger.warning("FAISS não disponível - busca vetorial desabilitada")
        except Exception as e:
            self.logger.error(f"Erro ao carregar FAISS: {str(e)}")

    async def _init_neo4j(self):
        """Inicializa conexão Neo4j."""
        try:
            from neo4j import GraphDatabase

            uri = self.neo4j_config.get("uri", "bolt://localhost:7687")
            username = self.neo4j_config.get("username", "neo4j")
            password = self.neo4j_config.get("password", "auditoria123")

            self.neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))

            # Testar conexão
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")

            self.logger.info("Conexão Neo4j estabelecida")

        except ImportError:
            self.logger.warning(
                "Neo4j driver não disponível - busca em grafo desabilitada"
            )
        except Exception as e:
            self.logger.warning(f"Neo4j não disponível: {str(e)}")

    # Métodos de busca NCM

    async def search_by_gtin(self, gtin: str) -> Optional[Dict[str, Any]]:
        """Busca produto por GTIN em exemplos conhecidos."""
        if not self.sqlite_conn:
            return None

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT gtin, descricao, ncm, cest
                FROM produtos_exemplos
                WHERE gtin = ?
            """,
                (gtin,),
            )

            result = cursor.fetchone()
            if result:
                return dict(result)

        except Exception as e:
            self.logger.error(f"Erro na busca por GTIN: {str(e)}")

        return None

    async def get_ncm_info(self, ncm: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um NCM específico."""
        if not self.sqlite_conn:
            return None

        cache_key = f"ncm_info_{ncm}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT codigo, descricao, capitulo, posicao, subposicao
                FROM ncm
                WHERE codigo = ?
            """,
                (ncm,),
            )

            result = cursor.fetchone()
            if result:
                ncm_info = dict(result)
                self._cache[cache_key] = ncm_info
                return ncm_info

        except Exception as e:
            self.logger.error(f"Erro na busca de NCM: {str(e)}")

        return None

    async def search_chapters(self, description: str) -> List[Dict[str, Any]]:
        """Busca capítulos NCM relevantes para uma descrição."""
        if not self.sqlite_conn:
            return []

        try:
            # Busca por palavras-chave na descrição
            keywords = self._extract_keywords(description)

            if not keywords:
                return []

            # Construir query de busca
            # placeholders removido (não utilizado)
            query = f"""
                SELECT DISTINCT capitulo,
                       GROUP_CONCAT(DISTINCT descricao) as descricoes,
                       COUNT(*) as total_ncms
                FROM ncm
                WHERE {' OR '.join(['descricao LIKE ?' for _ in keywords])}
                GROUP BY capitulo
                ORDER BY total_ncms DESC
                LIMIT 10
            """

            like_keywords = [f"%{keyword}%" for keyword in keywords]

            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, like_keywords)

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "codigo": row[0],
                        "descricao": row[1],
                        "score": min(row[2] / 100.0, 1.0),  # Normalizar score
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca de capítulos: {str(e)}")
            return []

    async def search_positions(
        self, description: str, chapter: str
    ) -> List[Dict[str, Any]]:
        """Busca posições NCM dentro de um capítulo."""
        if not self.sqlite_conn:
            return []

        try:
            keywords = self._extract_keywords(description)

            if not keywords:
                return []

            # placeholders removido (não utilizado)
            query = f"""
                SELECT DISTINCT posicao,
                       GROUP_CONCAT(DISTINCT descricao) as descricoes,
                       COUNT(*) as relevance
                FROM ncm
                WHERE capitulo = ? AND ({' OR '.join(['descricao LIKE ?' for _ in keywords])})
                GROUP BY posicao
                ORDER BY relevance DESC
                LIMIT 10
            """

            params = [chapter] + [f"%{keyword}%" for keyword in keywords]

            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "codigo": row[0],
                        "descricao": row[1],
                        "score": min(row[2] / 10.0, 1.0),
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca de posições: {str(e)}")
            return []

    async def search_subpositions(
        self, description: str, position: str
    ) -> List[Dict[str, Any]]:
        """Busca subposições NCM dentro de uma posição."""
        if not self.sqlite_conn:
            return []

        try:
            keywords = self._extract_keywords(description)

            query = f"""
                SELECT DISTINCT subposicao, descricao,
                       CASE
                           WHEN {' OR '.join(['descricao LIKE ?' for _ in keywords])} THEN 1
                           ELSE 0.5
                       END as score
                FROM ncm
                WHERE posicao = ?
                ORDER BY score DESC
                LIMIT 10
            """

            params = [f"%{keyword}%" for keyword in keywords] + [position]

            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({"codigo": row[0], "descricao": row[1], "score": row[2]})

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca de subposições: {str(e)}")
            return []

    async def search_items(
        self, description: str, subposition: str
    ) -> List[Dict[str, Any]]:
        """Busca itens NCM específicos dentro de uma subposição."""
        if not self.sqlite_conn:
            return []

        try:
            keywords = self._extract_keywords(description)

            query = f"""
                SELECT codigo, descricao,
                       CASE
                           WHEN {' OR '.join(['descricao LIKE ?' for _ in keywords])} THEN 0.9
                           ELSE 0.6
                       END as score
                FROM ncm
                WHERE subposicao = ?
                ORDER BY score DESC
                LIMIT 5
            """

            params = [f"%{keyword}%" for keyword in keywords] + [subposition]

            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({"codigo": row[0], "descricao": row[1], "score": row[2]})

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca de itens: {str(e)}")
            return []

    # Métodos de busca CEST

    async def get_cest_info(
        self, cest: str, estado: str = "RO"
    ) -> Optional[Dict[str, Any]]:
        """Busca informações de um CEST específico."""
        if not self.sqlite_conn:
            return None

        cache_key = f"cest_info_{cest}_{estado}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT cr.cest, cr.descricao, cr.situacao,
                       cr.vigencia_inicio, cr.vigencia_fim,
                       s.descricao as segmento
                FROM cest_regras cr
                LEFT JOIN segmentos s ON cr.segmento_id = s.id
                WHERE cr.cest = ?
            """,
                (cest,),
            )

            result = cursor.fetchone()
            if result:
                cest_info = dict(result)
                self._cache[cache_key] = cest_info
                return cest_info

        except Exception as e:
            self.logger.error(f"Erro na busca de CEST: {str(e)}")

        return None

    async def search_cest_by_ncm(
        self, ncm: str, estado: str = "RO"
    ) -> List[Dict[str, Any]]:
        """Busca CESTs por correspondência exata de NCM."""
        if not self.sqlite_conn:
            return []

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT cr.cest, cr.descricao, s.descricao as segmento,
                       nca.ncm_pattern
                FROM ncm_cest_associacao nca
                JOIN cest_regras cr ON nca.cest_codigo = cr.cest
                LEFT JOIN segmentos s ON cr.segmento_id = s.id
                WHERE nca.ncm_pattern = ?
                ORDER BY cr.cest
            """,
                (ncm,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "cest": row[0],
                        "descricao": row[1],
                        "segmento": row[2],
                        "ncm_pattern": row[3],
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca CEST por NCM: {str(e)}")
            return []

    async def search_cest_by_pattern(
        self, ncm_pattern: str, estado: str = "RO"
    ) -> List[Dict[str, Any]]:
        """Busca CESTs por padrão NCM (hierárquico)."""
        if not self.sqlite_conn:
            return []

        try:
            cursor = self.sqlite_conn.cursor()

            # Buscar padrões que correspondem ao NCM
            cursor.execute(
                """
                SELECT DISTINCT cr.cest, cr.descricao, s.descricao as segmento,
                       nca.ncm_pattern, LENGTH(nca.ncm_pattern) as pattern_specificity
                FROM ncm_cest_associacao nca
                JOIN cest_regras cr ON nca.cest_codigo = cr.cest
                LEFT JOIN segmentos s ON cr.segmento_id = s.id
                WHERE ? LIKE nca.ncm_pattern || '%'
                ORDER BY pattern_specificity DESC, cr.cest
            """,
                (ncm_pattern,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "cest": row[0],
                        "descricao": row[1],
                        "segmento": row[2],
                        "ncm_pattern": row[3],
                        "specificity": row[4],
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca CEST por padrão: {str(e)}")
            return []

    async def get_cest_ncm_rules(
        self, cest: str, estado: str = "RO"
    ) -> List[Dict[str, Any]]:
        """Busca todas as regras NCM de um CEST específico."""
        if not self.sqlite_conn:
            return []

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT ncm_pattern
                FROM ncm_cest_associacao
                WHERE cest_codigo = ?
                ORDER BY ncm_pattern
            """,
                (cest,),
            )

            results = []
            for row in cursor.fetchall():
                results.append({"ncm_pattern": row[0]})

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca de regras CEST: {str(e)}")
            return []

    # Busca semântica (quando disponível)

    async def semantic_search_products(
        self, description: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca semântica por produtos similares."""
        if not self.embeddings_model or not self.sqlite_conn:
            return []

        try:
            # Buscar produtos na base
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT descricao, ncm, cest
                FROM produtos_exemplos
                WHERE descricao IS NOT NULL
                LIMIT 1000
            """
            )

            products = cursor.fetchall()
            if not products:
                return []

            # Gerar embeddings
            descriptions = [p[0] for p in products]
            query_embedding = self.embeddings_model.encode([description])
            doc_embeddings = self.embeddings_model.encode(descriptions)

            # Calcular similaridades
            from sklearn.metrics.pairwise import cosine_similarity

            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]

            # Ordenar por similaridade
            ranked_indices = similarities.argsort()[::-1][:top_k]

            results = []
            for idx in ranked_indices:
                if similarities[idx] > 0.3:  # Threshold mínimo
                    results.append(
                        {
                            "descricao": products[idx][0],
                            "ncm": products[idx][1],
                            "cest": products[idx][2],
                            "score": float(similarities[idx]),
                        }
                    )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca semântica: {str(e)}")
            return []

    async def semantic_search_cest(
        self, description: str, estado: str = "RO", top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca semântica por CESTs relevantes."""
        # Implementação simplificada - pode ser expandida
        if not self.sqlite_conn:
            return []

        try:
            keywords = self._extract_keywords(description)

            cursor = self.sqlite_conn.cursor()
            query = f"""
                SELECT DISTINCT cr.cest, cr.descricao, s.descricao as segmento
                FROM cest_regras cr
                LEFT JOIN segmentos s ON cr.segmento_id = s.id
                WHERE {' OR '.join(['cr.descricao LIKE ?' for _ in keywords])}
                LIMIT ?
            """

            params = [f"%{keyword}%" for keyword in keywords] + [top_k]
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "cest": row[0],
                        "descricao": row[1],
                        "segmento": row[2],
                        "score": 0.7,  # Score fixo para busca por keywords
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca semântica CEST: {str(e)}")
            return []

    async def search_golden_set(
        self, description: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Busca no Golden Set por descrições similares."""
        if not self.sqlite_conn:
            return []

        try:
            # Verificar se tabela golden_set existe
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='golden_set'
            """
            )

            if not cursor.fetchone():
                return []

            keywords = self._extract_keywords(description)

            query = f"""
                SELECT descricao_produto, descricao_enriquecida, gtin,
                       ncm_correto, cest_correto, fonte_usuario
                FROM golden_set
                WHERE {' OR '.join(['descricao_produto LIKE ?' for _ in keywords])}
                   OR {' OR '.join(['descricao_enriquecida LIKE ?' for _ in keywords])}
                LIMIT ?
            """

            params = [f"%{keyword}%" for keyword in keywords] * 2 + [top_k]
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "descricao_original": row[0],
                        "descricao_enriquecida": row[1],
                        "gtin": row[2],
                        "ncm": row[3],
                        "cest": row[4],
                        "fonte": row[5],
                        "score": 0.8,  # Score alto para Golden Set
                    }
                )

            return results

        except Exception as e:
            self.logger.error(f"Erro na busca no Golden Set: {str(e)}")
            return []

    # Métodos utilitários

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave relevantes de um texto."""
        import re

        # Remover stopwords
        stopwords = {
            "de",
            "da",
            "do",
            "das",
            "dos",
            "em",
            "na",
            "no",
            "nas",
            "nos",
            "para",
            "por",
            "com",
            "sem",
            "sob",
            "sobre",
            "entre",
            "contra",
            "e",
            "ou",
            "mas",
            "que",
            "se",
            "o",
            "a",
            "os",
            "as",
            "um",
            "uma",
        }

        # Extrair palavras alfanuméricas com 3+ caracteres
        words = re.findall(r"\b[a-záàâãéèêíìîóòôõúùûç]{3,}\b", text.lower())

        # Filtrar stopwords
        keywords = [word for word in words if word not in stopwords]

        return keywords[:10]  # Limitar a 10 keywords

    def _manage_cache(self):
        """Gerencia o cache removendo entradas antigas."""
        if len(self._cache) > self._cache_size_limit:
            # Remover 20% das entradas mais antigas
            items_to_remove = int(self._cache_size_limit * 0.2)
            keys_to_remove = list(self._cache.keys())[:items_to_remove]

            for key in keys_to_remove:
                del self._cache[key]

    async def close(self):
        """Fecha todas as conexões."""
        if self.sqlite_conn:
            self.sqlite_conn.close()

        if self.neo4j_driver:
            self.neo4j_driver.close()

        self.logger.info("RetrievalTools fechado")
