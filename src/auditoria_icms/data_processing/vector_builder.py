"""
Vector Builder para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pela criação de embeddings e índices vetoriais para RAG
"""

import os
import json
import numpy as np
from typing import List, Dict, Any
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VectorBuilder:
    """Classe para construção de vetores e índices para RAG"""

    def __init__(
        self,
        processed_dir: str = None,
        embedding_model: str = None,
        vector_dim: int = 384,
    ):
        self.processed_dir = processed_dir or "./data/processed"
        self.embedding_model = embedding_model or "all-MiniLM-L6-v2"
        self.vector_dim = vector_dim

        # Inicializa modelo de embeddings
        self.encoder = self._initialize_encoder()

        # Armazena documentos e vetores
        self.documents = []
        self.embeddings = []
        self.metadata = []

    def _initialize_encoder(self):
        """Inicializa o modelo de embeddings."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Carregando modelo de embeddings: {self.embedding_model}")
            encoder = SentenceTransformer(self.embedding_model)
            logger.info(
                f"Modelo carregado. Dimensão dos vetores: {encoder.get_sentence_embedding_dimension()}"
            )
            return encoder
        except ImportError:
            logger.warning("sentence-transformers não disponível, usando simulação")
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return None

    def create_document_chunks(
        self, text: str, chunk_size: int = 512, overlap: int = 50
    ) -> List[str]:
        """Divide texto em chunks para vetorização."""
        if not text or len(text) < chunk_size:
            return [text] if text else []

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            if i + chunk_size >= len(words):
                break

        return chunks

    def process_ncm_descriptions(self) -> List[Dict]:
        """Processa descrições NCM para vetorização."""
        logger.info("Processando descrições NCM...")

        documents = []

        # Carrega dados NCM processados (simulação para agora)
        ncm_data = [
            {
                "codigo": "30049069",
                "descricao": "Outros medicamentos constituídos por produtos misturados ou não misturados",
            },
            {
                "codigo": "85171211",
                "descricao": "Telefones móveis e de outras redes sem fio",
            },
            {
                "codigo": "22021000",
                "descricao": "Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar",
            },
        ]

        for item in ncm_data:
            # Cria documento com contexto hierárquico
            codigo = item["codigo"]
            descricao = item["descricao"]

            # Extrai hierarquia
            capitulo = codigo[:2]
            posicao = codigo[:4]
            subposicao = codigo[:6]

            # Cria texto enriquecido
            enhanced_text = (
                f"NCM {codigo}: {descricao}. "
                f"Capítulo {capitulo}, Posição {posicao}, Subposição {subposicao}."
            )

            documents.append(
                {
                    "doc_id": f"ncm_{codigo}",
                    "doc_type": "ncm_description",
                    "content": enhanced_text,
                    "metadata": {
                        "ncm_codigo": codigo,
                        "capitulo": capitulo,
                        "posicao": posicao,
                        "subposicao": subposicao,
                        "descricao_original": descricao,
                    },
                }
            )

        logger.info(f"Processadas {len(documents)} descrições NCM")
        return documents

    def process_cest_rules(self) -> List[Dict]:
        """Processa regras CEST para vetorização."""
        logger.info("Processando regras CEST...")

        documents = []

        # Dados CEST simulados
        cest_data = [
            {
                "cest": "28.064.00",
                "descricao": "Artigos de vestuário infantil",
                "segmento": "Vestuário",
            },
            {
                "cest": "17.004.00",
                "descricao": "Medicamentos genéricos",
                "segmento": "Medicamentos",
            },
            {
                "cest": "21.001.00",
                "descricao": "Aparelhos telefônicos",
                "segmento": "Telecomunicações",
            },
        ]

        for item in cest_data:
            cest_codigo = item["cest"]
            descricao = item["descricao"]
            segmento = item["segmento"]

            # Cria texto enriquecido
            enhanced_text = (
                f"CEST {cest_codigo}: {descricao}. Segmento: {segmento}. "
                "Aplicável para substituição tributária."
            )

            documents.append(
                {
                    "doc_id": f"cest_{cest_codigo}",
                    "doc_type": "cest_rule",
                    "content": enhanced_text,
                    "metadata": {
                        "cest_codigo": cest_codigo,
                        "segmento": segmento,
                        "descricao_original": descricao,
                    },
                }
            )

        logger.info(f"Processadas {len(documents)} regras CEST")
        return documents

    def process_product_examples(self) -> List[Dict]:
        """Processa exemplos de produtos para vetorização."""
        logger.info("Processando exemplos de produtos...")

        documents = []

        # Carrega produtos enriquecidos se disponível
        products_file = os.path.join(self.processed_dir, "test_enriched_products.json")

        if os.path.exists(products_file):
            with open(products_file, "r", encoding="utf-8") as f:
                products_data = json.load(f)

            # Processa amostra dos produtos (primeiros 100 para teste)
            sample_products = products_data[:100]

            for i, product in enumerate(sample_products):
                descricao = product.get("descricao", "")
                ncm = product.get("ncm", "")
                marca = product.get("marca_extraida", "")
                categoria = product.get("categoria_inferida", "")

                # Cria texto enriquecido
                enhanced_text = f"Produto: {descricao}"
                if marca:
                    enhanced_text += f" Marca: {marca}"
                if categoria:
                    enhanced_text += f" Categoria: {categoria}"
                if ncm:
                    enhanced_text += f" NCM: {ncm}"

                documents.append(
                    {
                        "doc_id": f"produto_{i}",
                        "doc_type": "product_example",
                        "content": enhanced_text,
                        "metadata": {
                            "descricao_original": descricao,
                            "ncm": ncm,
                            "marca": marca,
                            "categoria": categoria,
                            "gtin": product.get("gtin", ""),
                        },
                    }
                )
        else:
            logger.warning("Arquivo de produtos enriquecidos não encontrado")

        logger.info(f"Processados {len(documents)} exemplos de produtos")
        return documents

    def process_nesh_notes(self) -> List[Dict]:
        """Processa notas NESH para vetorização."""
        logger.info("Processando notas NESH...")

        documents = []

        # Carrega notas NESH extraídas
        nesh_file = os.path.join(self.processed_dir, "extracted_documents.json")

        if os.path.exists(nesh_file):
            with open(nesh_file, "r", encoding="utf-8") as f:
                extracted_data = json.load(f)

            nesh_notes = extracted_data.get("nesh_notes", [])

            for note in nesh_notes:
                titulo = note.get("titulo", "")
                texto = note.get("texto", "")
                codigo_ref = note.get("codigo_referencia", "")
                tipo_ref = note.get("tipo_referencia", "")

                # Cria texto enriquecido
                enhanced_text = f"{titulo}. {texto}"
                if codigo_ref != "geral":
                    enhanced_text += f" Referência: {codigo_ref} ({tipo_ref})"

                documents.append(
                    {
                        "doc_id": f"nesh_{note.get('id')}",
                        "doc_type": "nesh_note",
                        "content": enhanced_text,
                        "metadata": {
                            "codigo_referencia": codigo_ref,
                            "tipo_referencia": tipo_ref,
                            "titulo": titulo,
                            "origem": note.get("origem", "NESH"),
                        },
                    }
                )
        else:
            logger.warning("Arquivo de notas NESH não encontrado")

        logger.info(f"Processadas {len(documents)} notas NESH")
        return documents

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Gera embeddings para lista de textos."""
        if self.encoder is None:
            # Simulação de embeddings se modelo não disponível
            logger.info("Gerando embeddings simulados...")
            embeddings = np.random.rand(len(texts), self.vector_dim).astype(np.float32)
            return embeddings

        try:
            logger.info(f"Gerando embeddings para {len(texts)} textos...")
            embeddings = self.encoder.encode(
                texts, convert_to_numpy=True, show_progress_bar=True
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings: {e}")
            # Fallback para simulação
            embeddings = np.random.rand(len(texts), self.vector_dim).astype(np.float32)
            return embeddings

    def build_vector_database(self) -> Dict:
        """Constrói base de dados vetorial completa."""
        logger.info("Construindo base de dados vetorial...")

        all_documents = []

        # Coleta todos os documentos
        all_documents.extend(self.process_ncm_descriptions())
        all_documents.extend(self.process_cest_rules())
        all_documents.extend(self.process_product_examples())
        all_documents.extend(self.process_nesh_notes())

        if not all_documents:
            logger.warning("Nenhum documento encontrado para vetorização")
            return {}

        # Extrai textos para embeddings
        texts = [doc["content"] for doc in all_documents]

        # Gera embeddings
        embeddings = self.generate_embeddings(texts)

        # Constrói índice
        vector_db = {
            "documents": all_documents,
            "embeddings": embeddings.tolist(),  # Converte para lista para JSON
            "metadata": {
                "total_documents": len(all_documents),
                "embedding_dimension": embeddings.shape[1],
                "model_name": self.embedding_model,
                "created_at": datetime.now().isoformat(),
                "document_types": {},
            },
        }

        # Estatísticas por tipo de documento
        for doc in all_documents:
            doc_type = doc["doc_type"]
            if doc_type not in vector_db["metadata"]["document_types"]:
                vector_db["metadata"]["document_types"][doc_type] = 0
            vector_db["metadata"]["document_types"][doc_type] += 1

        logger.info("Base vetorial construída:")
        logger.info(f"- Total de documentos: {len(all_documents)}")
        logger.info(f"- Dimensão dos embeddings: {embeddings.shape[1]}")
        logger.info(f"- Tipos de documento: {vector_db['metadata']['document_types']}")

        return vector_db

    def create_faiss_index(self, embeddings: np.ndarray) -> Any:
        """Cria índice FAISS para busca vetorial eficiente."""
        try:
            import faiss

            # Normaliza embeddings
            faiss.normalize_L2(embeddings)

            # Cria índice FAISS
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
            index.add(embeddings)

            logger.info(f"Índice FAISS criado com {index.ntotal} vetores")
            return index

        except ImportError:
            logger.warning("FAISS não disponível, usando busca linear")
            return None
        except Exception as e:
            logger.error(f"Erro ao criar índice FAISS: {e}")
            return None

    def save_vector_database(self, vector_db: Dict, faiss_index: Any = None):
        """Salva base de dados vetorial."""
        os.makedirs(self.processed_dir, exist_ok=True)

        # Salva metadados e documentos
        vector_db_file = os.path.join(self.processed_dir, "vector_database.json")

        # Separa embeddings para arquivo binário (mais eficiente)
        embeddings = np.array(vector_db["embeddings"])
        vector_db_save = vector_db.copy()
        del vector_db_save["embeddings"]  # Remove embeddings do JSON

        with open(vector_db_file, "w", encoding="utf-8") as f:
            json.dump(vector_db_save, f, indent=2, ensure_ascii=False)

        # Salva embeddings em formato binário
        embeddings_file = os.path.join(self.processed_dir, "embeddings.npy")
        np.save(embeddings_file, embeddings)

        # Salva índice FAISS se disponível
        if faiss_index is not None:
            try:
                import faiss

                faiss_file = os.path.join(self.processed_dir, "faiss_index.bin")
                faiss.write_index(faiss_index, faiss_file)
                logger.info(f"Índice FAISS salvo: {faiss_file}")
            except Exception as e:
                logger.error(f"Erro ao salvar índice FAISS: {e}")

        logger.info("Base vetorial salva:")
        logger.info(f"- Metadados: {vector_db_file}")
        logger.info(f"- Embeddings: {embeddings_file}")

    def run_vector_building_test(self):
        """Executa teste completo de construção vetorial."""
        logger.info("=== Teste de Construção Vetorial ===")

        # Constrói base vetorial
        vector_db = self.build_vector_database()

        if not vector_db:
            logger.error("Falha na construção da base vetorial")
            return False

        # Converte embeddings para numpy
        embeddings = np.array(vector_db["embeddings"])

        # Cria índice FAISS
        faiss_index = self.create_faiss_index(embeddings.copy())

        # Salva tudo
        self.save_vector_database(vector_db, faiss_index)

        # Teste de busca simples
        if self.encoder is not None:
            self.test_vector_search(vector_db, embeddings)

        logger.info("=== Teste de Construção Vetorial Concluído ===")
        return True

    def test_vector_search(self, vector_db: Dict, embeddings: np.ndarray):
        """Testa busca vetorial."""
        logger.info("Testando busca vetorial...")

        # Query de teste
        query = "medicamento para dor de cabeça"

        try:
            # Gera embedding da query
            query_embedding = self.generate_embeddings([query])[0]

            # Calcula similaridades
            similarities = np.dot(embeddings, query_embedding)

            # Encontra top 3 mais similares
            top_indices = np.argsort(similarities)[-3:][::-1]

            logger.info(f"Resultado da busca para '{query}':")
            for i, idx in enumerate(top_indices):
                doc = vector_db["documents"][idx]
                score = similarities[idx]
                logger.info(
                    f"{i+1}. [{doc['doc_type']}] {doc['content'][:100]}... (score: {score:.3f})"
                )

        except Exception as e:
            logger.error(f"Erro no teste de busca: {e}")


def main():
    """Função principal para teste."""
    builder = VectorBuilder()
    builder.run_vector_building_test()


if __name__ == "__main__":
    main()
