"""
Processador de dados farmacêuticos - Tabela ABC Farma
Responsável por processar medicamentos do capítulo 30 NCM e segmento 13 CEST
"""

import pandas as pd
import json
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FarmaProcessor:
    """
    Processador especializado para dados farmacêuticos
    Processa Tabela_ABC_Farma.xlsx com medicamentos NCM 3003/3004 e CEST segmento 13
    """

    def __init__(self, data_path: str = "data/raw"):
        self.data_path = Path(data_path)
        self.farma_data = None
        self.processed_data = {}

    def load_tabela_abc_farma(self) -> pd.DataFrame:
        """
        Carrega dados da Tabela_ABC_Farma.xlsx
        Contém medicamentos com descrição completa e código de barras
        """
        try:
            farma_file = self.data_path / "Tabela_ABC_Farma.xlsx"

            if not farma_file.exists():
                logger.warning(
                    f"Arquivo {farma_file} não encontrado. Criando dados de exemplo..."
                )
                return self._create_sample_farma_data()

            # Carrega a planilha
            df = pd.read_excel(farma_file)

            # Normaliza nomes das colunas
            df.columns = df.columns.str.lower().str.strip()

            # Valida colunas obrigatórias
            required_columns = ["codigo_barras", "descricao", "ncm", "cest"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                logger.error(f"Colunas obrigatórias ausentes: {missing_columns}")
                return pd.DataFrame()

            # Filtra medicamentos (NCM 3003 ou 3004)
            df = df[df["ncm"].astype(str).str.startswith(("3003", "3004"))]

            # Valida CEST segmento 13
            df = df[df["cest"].astype(str).str.startswith("13.")]

            logger.info(f"Carregados {len(df)} medicamentos da Tabela ABC Farma")
            self.farma_data = df
            return df

        except Exception as e:
            logger.error(f"Erro ao carregar Tabela_ABC_Farma: {str(e)}")
            return pd.DataFrame()

    def _create_sample_farma_data(self) -> pd.DataFrame:
        """
        Cria dados de exemplo para medicamentos farmacêuticos
        """
        sample_data = [
            {
                "codigo_barras": "7891234567890",
                "descricao": "DIPIRONA SÓDICA 500MG COMPRIMIDO",
                "ncm": "3004.90.69",
                "cest": "13.001.00",
                "principio_ativo": "DIPIRONA SÓDICA",
                "concentracao": "500MG",
                "forma_farmaceutica": "COMPRIMIDO",
            },
            {
                "codigo_barras": "7891234567891",
                "descricao": "PARACETAMOL 750MG COMPRIMIDO",
                "ncm": "3004.90.69",
                "cest": "13.001.00",
                "principio_ativo": "PARACETAMOL",
                "concentracao": "750MG",
                "forma_farmaceutica": "COMPRIMIDO",
            },
            {
                "codigo_barras": "7891234567892",
                "descricao": "IBUPROFENO 600MG COMPRIMIDO REVESTIDO",
                "ncm": "3004.90.69",
                "cest": "13.001.00",
                "principio_ativo": "IBUPROFENO",
                "concentracao": "600MG",
                "forma_farmaceutica": "COMPRIMIDO REVESTIDO",
            },
            {
                "codigo_barras": "7891234567893",
                "descricao": "AMOXICILINA 875MG + CLAVULANATO DE POTÁSSIO 125MG COMPRIMIDO",
                "ncm": "3004.20.59",
                "cest": "13.002.00",
                "principio_ativo": "AMOXICILINA + CLAVULANATO",
                "concentracao": "875MG + 125MG",
                "forma_farmaceutica": "COMPRIMIDO",
            },
            {
                "codigo_barras": "7891234567894",
                "descricao": "OMEPRAZOL 20MG CÁPSULA DE LIBERAÇÃO RETARDADA",
                "ncm": "3004.90.69",
                "cest": "13.001.00",
                "principio_ativo": "OMEPRAZOL",
                "concentracao": "20MG",
                "forma_farmaceutica": "CÁPSULA",
            },
        ]

        df = pd.DataFrame(sample_data)
        logger.info(f"Criados {len(df)} registros de exemplo para medicamentos")
        return df

    def process_medicamentos(self) -> Dict:
        """
        Processa dados de medicamentos para classificação NCM/CEST
        """
        if self.farma_data is None:
            self.load_tabela_abc_farma()

        if self.farma_data.empty:
            return {}

        processed = {
            "medicamentos_por_ncm": {},
            "medicamentos_por_cest": {},
            "medicamentos_por_codigo_barras": {},
            "padroes_descricao": {},
            "estatisticas": {},
        }

        # Agrupa por NCM
        for ncm in self.farma_data["ncm"].unique():
            ncm_data = self.farma_data[self.farma_data["ncm"] == ncm]
            processed["medicamentos_por_ncm"][ncm] = {
                "count": len(ncm_data),
                "medicamentos": ncm_data.to_dict("records"),
                "descricoes_unicas": ncm_data["descricao"].unique().tolist(),
            }

        # Agrupa por CEST
        for cest in self.farma_data["cest"].unique():
            cest_data = self.farma_data[self.farma_data["cest"] == cest]
            processed["medicamentos_por_cest"][cest] = {
                "count": len(cest_data),
                "medicamentos": cest_data.to_dict("records"),
                "ncms_relacionados": cest_data["ncm"].unique().tolist(),
            }

        # Índice por código de barras
        for _, row in self.farma_data.iterrows():
            processed["medicamentos_por_codigo_barras"][row["codigo_barras"]] = {
                "descricao": row["descricao"],
                "ncm": row["ncm"],
                "cest": row["cest"],
                "detalhes": row.to_dict(),
            }

        # Identifica padrões nas descrições
        processed["padroes_descricao"] = self._analyze_description_patterns()

        # Estatísticas gerais
        processed["estatisticas"] = {
            "total_medicamentos": len(self.farma_data),
            "ncms_unicos": len(self.farma_data["ncm"].unique()),
            "cests_unicos": len(self.farma_data["cest"].unique()),
            "codigos_barras_unicos": len(self.farma_data["codigo_barras"].unique()),
        }

        self.processed_data = processed
        return processed

    def _analyze_description_patterns(self) -> Dict:
        """
        Analisa padrões nas descrições dos medicamentos
        """
        if self.farma_data is None or self.farma_data.empty:
            return {}

        patterns = {
            "formas_farmaceuticas": {},
            "concentracoes": {},
            "principios_ativos": {},
        }

        # Identifica formas farmacêuticas
        formas = [
            "COMPRIMIDO",
            "CÁPSULA",
            "SOLUÇÃO",
            "SUSPENSÃO",
            "XAROPE",
            "GOTAS",
            "POMADA",
            "CREME",
        ]
        for forma in formas:
            count = (
                self.farma_data["descricao"]
                .str.contains(forma, case=False, na=False)
                .sum()
            )
            if count > 0:
                patterns["formas_farmaceuticas"][forma] = count

        # Identifica padrões de concentração
        import re

        concentracoes = []
        for desc in self.farma_data["descricao"]:
            matches = re.findall(
                r"\d+(?:\.\d+)?(?:MG|G|ML|%)", str(desc), re.IGNORECASE
            )
            concentracoes.extend(matches)

        for conc in set(concentracoes):
            patterns["concentracoes"][conc] = concentracoes.count(conc)

        return patterns

    def search_medicamento_by_description(
        self, descricao: str, similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """
        Busca medicamentos por similaridade de descrição
        """
        if self.farma_data is None:
            self.load_tabela_abc_farma()

        if self.farma_data.empty:
            return []

        # Busca por correspondência exata primeiro
        exact_matches = self.farma_data[
            self.farma_data["descricao"].str.contains(descricao, case=False, na=False)
        ]

        if not exact_matches.empty:
            return exact_matches.to_dict("records")

        # Busca por similaridade usando palavras-chave
        descricao_words = set(descricao.upper().split())
        similar_matches = []

        for _, row in self.farma_data.iterrows():
            row_words = set(str(row["descricao"]).upper().split())
            intersection = descricao_words.intersection(row_words)
            similarity = len(intersection) / len(descricao_words.union(row_words))

            if similarity >= similarity_threshold:
                match_data = row.to_dict()
                match_data["similarity_score"] = similarity
                similar_matches.append(match_data)

        # Ordena por similaridade
        similar_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_matches[:5]  # Top 5 matches

    def get_ncm_cest_suggestions(self, descricao: str) -> Dict:
        """
        Sugere NCM e CEST com base na descrição do produto farmacêutico
        """
        matches = self.search_medicamento_by_description(descricao)

        if not matches:
            return {
                "ncm_sugerido": None,
                "cest_sugerido": None,
                "confianca": 0,
                "justificativa": "Nenhum medicamento similar encontrado na base ABC Farma",
            }

        # Pega o melhor match
        best_match = matches[0]

        return {
            "ncm_sugerido": best_match["ncm"],
            "cest_sugerido": best_match["cest"],
            "confianca": best_match.get("similarity_score", 1.0),
            "justificativa": f"Baseado em medicamento similar: {best_match['descricao']}",
            "medicamento_referencia": best_match,
            "alternativas": matches[1:3] if len(matches) > 1 else [],
        }

    def export_processed_data(self, output_path: str = "data/processed") -> str:
        """
        Exporta dados processados para arquivo JSON
        """
        if not self.processed_data:
            self.process_medicamentos()

        output_file = Path(output_path) / "tabela_abc_farma_processed.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.processed_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Dados processados exportados para: {output_file}")
        return str(output_file)


def main():
    """Função principal para teste do processador"""
    processor = FarmaProcessor()

    # Carrega e processa dados
    df = processor.load_tabela_abc_farma()
    print(f"Carregados {len(df)} medicamentos")

    # Processa dados
    processed = processor.process_medicamentos()
    print("Processamento concluído:")
    print(f"- NCMs únicos: {processed['estatisticas']['ncms_unicos']}")
    print(f"- CESTs únicos: {processed['estatisticas']['cests_unicos']}")

    # Teste de busca
    test_desc = "DIPIRONA COMPRIMIDO"
    suggestions = processor.get_ncm_cest_suggestions(test_desc)
    print(f"\nSugestões para '{test_desc}':")
    print(f"NCM: {suggestions['ncm_sugerido']}")
    print(f"CEST: {suggestions['cest_sugerido']}")
    print(f"Confiança: {suggestions['confianca']:.2f}")

    # Exporta dados
    output_file = processor.export_processed_data()
    print(f"\nDados exportados para: {output_file}")


if __name__ == "__main__":
    main()
