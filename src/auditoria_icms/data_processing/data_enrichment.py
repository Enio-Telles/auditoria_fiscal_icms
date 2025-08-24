"""
Data Enrichment para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pelo enriquecimento e normalização dos dados extraídos
"""

import pandas as pd
import json
import re
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataEnrichment:
    """Classe para enriquecimento e normalização de dados"""

    def __init__(self, data_dir: str = None, processed_dir: str = None):
        self.data_dir = data_dir or "./data/raw"
        self.processed_dir = processed_dir or "./data/processed"

        # Dicionários de enriquecimento
        self.brand_mappings = self._load_brand_mappings()
        self.category_mappings = self._load_category_mappings()
        self.synonym_mappings = self._load_synonym_mappings()

    def _load_brand_mappings(self) -> Dict[str, str]:
        """Carrega mapeamentos de marcas conhecidas."""
        return {
            "nestle": "Nestlé",
            "unilever": "Unilever",
            "pepsico": "PepsiCo",
            "cocacola": "Coca-Cola",
            "ambev": "Ambev",
            "bayer": "Bayer",
            "pfizer": "Pfizer",
            "roche": "Roche",
            "johnson": "Johnson & Johnson",
            "samsung": "Samsung",
            "lg": "LG Electronics",
            "philips": "Philips",
            "sony": "Sony",
            "microsoft": "Microsoft",
            "apple": "Apple",
            "google": "Google",
            "amazon": "Amazon",
        }

    def _load_category_mappings(self) -> Dict[str, List[str]]:
        """Carrega mapeamentos de categorias por palavras-chave."""
        return {
            "medicamentos": [
                "medicamento",
                "remedio",
                "farmaco",
                "comprimido",
                "capsula",
                "xarope",
                "antibiotico",
            ],
            "alimentos": [
                "alimento",
                "comida",
                "bebida",
                "leite",
                "queijo",
                "pao",
                "biscoito",
                "chocolate",
            ],
            "cosmeticos": [
                "cosmetico",
                "perfume",
                "shampoo",
                "sabonete",
                "creme",
                "maquiagem",
                "batom",
            ],
            "eletronicos": [
                "eletronico",
                "celular",
                "smartphone",
                "tablet",
                "computador",
                "televisao",
                "radio",
            ],
            "vestuario": [
                "roupa",
                "camisa",
                "calca",
                "vestido",
                "sapato",
                "tenis",
                "bolsa",
                "carteira",
            ],
            "casa_jardim": [
                "movel",
                "mesa",
                "cadeira",
                "sofa",
                "cama",
                "geladeira",
                "fogao",
                "microondas",
            ],
            "automotivo": [
                "carro",
                "automovel",
                "peca",
                "pneu",
                "oleo",
                "filtro",
                "bateria",
                "motor",
            ],
            "esporte": [
                "esporte",
                "bola",
                "tenis",
                "bicicleta",
                "equipamento",
                "academia",
                "fitness",
            ],
            "livros_midias": [
                "livro",
                "revista",
                "jornal",
                "cd",
                "dvd",
                "bluray",
                "game",
                "jogo",
            ],
            "brinquedos": [
                "brinquedo",
                "boneca",
                "carrinho",
                "jogo",
                "infantil",
                "crianca",
            ],
        }

    def _load_synonym_mappings(self) -> Dict[str, List[str]]:
        """Carrega mapeamentos de sinônimos."""
        return {
            "smartphone": ["celular", "telefone celular", "telefone móvel", "mobile"],
            "tablet": ["tablete", "computador tablet"],
            "televisão": ["tv", "televisor", "aparelho de tv"],
            "geladeira": ["refrigerador", "frigorífico"],
            "fogão": ["fogao", "cooktop"],
            "microondas": ["micro-ondas", "forno microondas"],
            "automóvel": ["carro", "veiculo", "automovel"],
            "medicamento": ["remedio", "farmaco", "medicina"],
            "cosmetico": ["cosmético", "produto de beleza"],
            "perfume": ["fragancia", "eau de toilette", "colonia"],
        }

    def extract_brand_from_description(self, description: str) -> Optional[str]:
        """Extrai marca da descrição do produto."""
        if not description:
            return None

        description_lower = description.lower()

        # Procura por marcas conhecidas
        for brand_key, brand_name in self.brand_mappings.items():
            if brand_key in description_lower:
                return brand_name

        # Tenta extrair marca usando padrões comuns
        # Padrão: "MARCA - produto" ou "produto MARCA"
        brand_patterns = [
            r"^([A-Z][A-Za-z]+)\s*[-–]\s*",  # Marca no início seguida de hífen
            r"\b([A-Z][A-Za-z]+)\s+\b",  # Palavra com primeira letra maiúscula
        ]

        for pattern in brand_patterns:
            matches = re.findall(pattern, description)
            if matches:
                potential_brand = matches[0]
                # Filtra palavras comuns que não são marcas
                common_words = {
                    "UNIDADE",
                    "PACOTE",
                    "CAIXA",
                    "FRASCO",
                    "TUBO",
                    "ML",
                    "MG",
                    "KG",
                    "G",
                }
                if (
                    potential_brand.upper() not in common_words
                    and len(potential_brand) > 2
                ):
                    return potential_brand.title()

        return None

    def categorize_product(self, description: str) -> Optional[str]:
        """Categoriza produto baseado na descrição."""
        if not description:
            return None

        description_lower = description.lower()

        # Calcula score para cada categoria
        category_scores = {}
        for category, keywords in self.category_mappings.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                category_scores[category] = score

        # Retorna categoria com maior score
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return "outros"

    def normalize_description(self, description: str) -> str:
        """Normaliza descrição do produto."""
        if not description:
            return ""

        # Remove caracteres especiais excessivos
        normalized = re.sub(r"[^\w\s\-\.\,\(\)\%]", " ", description)

        # Remove espaços múltiplos
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove números de lote/código no final
        normalized = re.sub(r"\b\d{6,}\b$", "", normalized)

        # Capitaliza primeira letra de cada palavra
        normalized = normalized.title()

        return normalized.strip()

    def extract_technical_specs(self, description: str) -> Dict[str, Any]:
        """Extrai especificações técnicas da descrição."""
        specs = {}

        if not description:
            return specs

        # Extrai peso/volume
        weight_patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:kg|quilos?)",
            r"(\d+(?:\.\d+)?)\s*(?:g|gramas?)",
            r"(\d+(?:\.\d+)?)\s*(?:mg|miligramas?)",
        ]

        volume_patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:l|litros?)",
            r"(\d+(?:\.\d+)?)\s*(?:ml|mililitros?)",
        ]

        # Busca peso
        for pattern in weight_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                specs["peso"] = float(match.group(1))
                specs["unidade_peso"] = pattern.split("?")[0].split("|")[-1].strip(")")
                break

        # Busca volume
        for pattern in volume_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                specs["volume"] = float(match.group(1))
                specs["unidade_volume"] = (
                    pattern.split("?")[0].split("|")[-1].strip(")")
                )
                break

        # Extrai concentração (para medicamentos)
        concentration_pattern = r"(\d+(?:\.\d+)?)\s*(?:mg|g)/(?:ml|l|g)"
        match = re.search(concentration_pattern, description, re.IGNORECASE)
        if match:
            specs["concentracao"] = float(match.group(1))

        return specs

    def enrich_product_data(self, product_data: Dict) -> Dict:
        """Enriquece dados de um produto individual."""
        enriched = product_data.copy()

        description = product_data.get("descricao", "")

        # Extrai e adiciona informações
        enriched["marca_extraida"] = self.extract_brand_from_description(description)
        enriched["categoria_inferida"] = self.categorize_product(description)
        enriched["descricao_normalizada"] = self.normalize_description(description)
        enriched["especificacoes_tecnicas"] = self.extract_technical_specs(description)

        # Adiciona metadados de enriquecimento
        enriched["enriched_at"] = datetime.now().isoformat()
        enriched["enrichment_version"] = "1.0"

        return enriched

    def enrich_products_dataset(self, products_df: pd.DataFrame) -> pd.DataFrame:
        """Enriquece um dataset completo de produtos."""
        logger.info(f"Enriquecendo dataset com {len(products_df)} produtos...")

        enriched_products = []

        for idx, row in products_df.iterrows():
            product_dict = row.to_dict()
            enriched_product = self.enrich_product_data(product_dict)
            enriched_products.append(enriched_product)

            if (idx + 1) % 1000 == 0:
                logger.info(f"Processados {idx + 1} produtos...")

        # Converte de volta para DataFrame
        enriched_df = pd.DataFrame(enriched_products)

        logger.info(
            f"Enriquecimento concluído: {len(enriched_df)} produtos processados"
        )

        return enriched_df

    def create_product_index(self, enriched_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Cria índices para busca rápida de produtos."""
        logger.info("Criando índices de produtos...")

        indices = {
            "por_marca": {},
            "por_categoria": {},
            "por_ncm": {},
            "por_palavras_chave": {},
        }

        for idx, row in enriched_df.iterrows():
            product_id = str(row.get("gtin", idx))

            # Índice por marca
            marca = row.get("marca_extraida")
            if marca:
                if marca not in indices["por_marca"]:
                    indices["por_marca"][marca] = []
                indices["por_marca"][marca].append(product_id)

            # Índice por categoria
            categoria = row.get("categoria_inferida")
            if categoria:
                if categoria not in indices["por_categoria"]:
                    indices["por_categoria"][categoria] = []
                indices["por_categoria"][categoria].append(product_id)

            # Índice por NCM
            ncm = row.get("ncm")
            if ncm:
                if ncm not in indices["por_ncm"]:
                    indices["por_ncm"][ncm] = []
                indices["por_ncm"][ncm].append(product_id)

            # Índice por palavras-chave
            descricao = row.get("descricao_normalizada", "")
            palavras = descricao.lower().split()
            for palavra in palavras:
                if len(palavra) > 3:  # Ignora palavras muito curtas
                    if palavra not in indices["por_palavras_chave"]:
                        indices["por_palavras_chave"][palavra] = []
                    if product_id not in indices["por_palavras_chave"][palavra]:
                        indices["por_palavras_chave"][palavra].append(product_id)

        logger.info("Índices criados com sucesso!")
        return indices

    def save_enriched_data(
        self, enriched_df: pd.DataFrame, indices: Dict, output_prefix: str = "enriched"
    ):
        """Salva dados enriquecidos e índices."""
        os.makedirs(self.processed_dir, exist_ok=True)

        # Salva DataFrame enriquecido
        products_file = os.path.join(
            self.processed_dir, f"{output_prefix}_products.json"
        )
        enriched_df.to_json(
            products_file, orient="records", indent=2, force_ascii=False
        )
        logger.info(f"Produtos enriquecidos salvos: {products_file}")

        # Salva índices
        indices_file = os.path.join(self.processed_dir, f"{output_prefix}_indices.json")
        with open(indices_file, "w", encoding="utf-8") as f:
            json.dump(indices, f, indent=2, ensure_ascii=False)
        logger.info(f"Índices salvos: {indices_file}")

        # Salva estatísticas
        stats = self.generate_enrichment_stats(enriched_df)
        stats_file = os.path.join(self.processed_dir, f"{output_prefix}_stats.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Estatísticas salvas: {stats_file}")

    def generate_enrichment_stats(self, enriched_df: pd.DataFrame) -> Dict:
        """Gera estatísticas do enriquecimento."""
        stats = {
            "total_produtos": len(enriched_df),
            "produtos_com_marca": len(
                enriched_df[enriched_df["marca_extraida"].notna()]
            ),
            "produtos_categorizados": len(
                enriched_df[enriched_df["categoria_inferida"].notna()]
            ),
            "distribuicao_categorias": enriched_df["categoria_inferida"]
            .value_counts()
            .to_dict(),
            "distribuicao_marcas": enriched_df["marca_extraida"]
            .value_counts()
            .head(20)
            .to_dict(),
            "ncms_unicos": (
                enriched_df["ncm"].nunique() if "ncm" in enriched_df.columns else 0
            ),
            "generated_at": datetime.now().isoformat(),
        }

        return stats

    def run_enrichment_test(self):
        """Executa teste completo de enriquecimento."""
        logger.info("=== Teste de Enriquecimento de Dados ===")

        # Carrega dados de produtos para teste
        products_file = os.path.join(self.data_dir, "produtos_selecionados.json")

        if os.path.exists(products_file):
            with open(products_file, "r", encoding="utf-8") as f:
                products_data = json.load(f)

            # Converte para DataFrame
            products_df = pd.DataFrame(products_data)
            logger.info(f"Carregados {len(products_df)} produtos para teste")

            # Executa enriquecimento
            enriched_df = self.enrich_products_dataset(products_df)

            # Cria índices
            indices = self.create_product_index(enriched_df)

            # Salva resultados
            self.save_enriched_data(enriched_df, indices, "test_enriched")

            # Exibe algumas estatísticas
            stats = self.generate_enrichment_stats(enriched_df)
            logger.info("Estatísticas do enriquecimento:")
            logger.info(f"- Total de produtos: {stats['total_produtos']}")
            logger.info(f"- Produtos com marca: {stats['produtos_com_marca']}")
            logger.info(f"- Produtos categorizados: {stats['produtos_categorizados']}")

        else:
            logger.warning(f"Arquivo de produtos não encontrado: {products_file}")

            # Teste com dados simulados
            test_products = [
                {
                    "descricao": "DIPIRONA SODICA 500MG COMPRIMIDO MEDLEY",
                    "gtin": "1234567890123",
                    "ncm": "30049069",
                },
                {
                    "descricao": "SMARTPHONE SAMSUNG GALAXY A54 128GB",
                    "gtin": "1234567890124",
                    "ncm": "85171211",
                },
                {
                    "descricao": "COCA-COLA 350ML LATA",
                    "gtin": "1234567890125",
                    "ncm": "22021000",
                },
            ]

            test_df = pd.DataFrame(test_products)
            enriched_df = self.enrich_products_dataset(test_df)

            logger.info("Teste com dados simulados concluído")
            logger.info(f"Produtos de teste enriquecidos: {len(enriched_df)}")

        logger.info("=== Teste de Enriquecimento Concluído ===")


def main():
    """Função principal para teste."""
    enricher = DataEnrichment()
    enricher.run_enrichment_test()


if __name__ == "__main__":
    main()
