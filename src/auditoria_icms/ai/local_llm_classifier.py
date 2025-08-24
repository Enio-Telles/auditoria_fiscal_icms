#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de IA Local com Ollama para Classificação NCM/CEST
=========================================================

Sistema 100% local usando Ollama para executar LLMs localmente.
Garante privacidade total e independência da internet.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
import pandas as pd

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Resultado da classificação de IA"""

    produto_id: str
    descricao: str
    ncm_sugerido: str
    ncm_confianca: float
    cest_sugerido: Optional[str]
    cest_confianca: float
    justificativa: str
    modelo_usado: str
    tempo_processamento: float
    categorias_identificadas: List[str]
    palavras_chave: List[str]


@dataclass
class OllamaConfig:
    """Configuração do Ollama"""

    base_url: str = "http://localhost:11434"
    modelo_principal: str = "llama3.1"
    modelo_backup: str = "llama2"
    timeout: int = 30
    max_retries: int = 3


class LocalLLMClassifier:
    """Classificador usando LLMs locais via Ollama"""

    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.ncm_data = None
        self.cest_data = None
        self.load_reference_data()

    def load_reference_data(self):
        """Carrega dados de referência NCM e CEST"""
        try:
            # Carregar dados NCM
            ncm_file = Path("data/raw/descricoes_ncm.json")
            if ncm_file.exists():
                with open(ncm_file, "r", encoding="utf-8") as f:
                    self.ncm_data = json.load(f)
                logger.info(f"Carregados {len(self.ncm_data)} códigos NCM")

            # Carregar dados CEST
            cest_file = Path("data/raw/CEST_RO.xlsx")
            if cest_file.exists():
                cest_df = pd.read_excel(cest_file)
                self.cest_data = cest_df.to_dict("records")
                logger.info(f"Carregados {len(self.cest_data)} códigos CEST")

        except Exception as e:
            logger.error(f"Erro ao carregar dados de referência: {e}")
            self.ncm_data = {}
            self.cest_data = []

    def check_ollama_connection(self) -> bool:
        """Verifica se o Ollama está rodando"""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Lista modelos disponíveis no Ollama"""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
        return []

    def ensure_model_available(self, model_name: str) -> bool:
        """Garante que o modelo está disponível, fazendo pull se necessário"""
        available_models = self.get_available_models()

        # Verificar se modelo já está disponível
        for available in available_models:
            if model_name in available:
                logger.info(f"Modelo {model_name} já disponível")
                return True

        # Fazer pull do modelo
        logger.info(f"Fazendo pull do modelo {model_name}...")
        try:
            response = requests.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model_name},
                timeout=300,  # 5 minutos para download
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao fazer pull do modelo {model_name}: {e}")
            return False

    def query_ollama(self, prompt: str, model: str = None) -> Optional[str]:
        """Faz consulta ao Ollama"""
        model = model or self.config.modelo_principal

        # Garantir que o modelo está disponível
        if not self.ensure_model_available(model):
            logger.warning(f"Modelo {model} não disponível, tentando backup")
            model = self.config.modelo_backup
            if not self.ensure_model_available(model):
                logger.error("Nenhum modelo disponível")
                return None

        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"Consultando Ollama (tentativa {attempt + 1}) - modelo: {model}"
                )

                response = requests.post(
                    f"{self.config.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Baixa criatividade para classificação
                            "top_p": 0.9,
                            "num_predict": 512,
                        },
                    },
                    timeout=self.config.timeout,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                else:
                    logger.error(f"Erro HTTP {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na tentativa {attempt + 1}")
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {e}")

        return None

    def create_classification_prompt(self, descricao: str) -> str:
        """Cria prompt específico para classificação NCM/CEST"""

        # Exemplos de produtos para few-shot learning
        exemplos = """
EXEMPLOS DE CLASSIFICAÇÃO:

Produto: "Notebook Dell Inspiron 15 Intel Core i5"
NCM: 8471.30.12 (Máquinas portáteis de processamento de dados)
CEST: 01.001.00 (Equipamentos de informática)
Justificativa: Computador portátil para processamento de dados

Produto: "Smartphone Samsung Galaxy A54"
NCM: 8517.12.31 (Telefones móveis)
CEST: 01.002.00 (Equipamentos de telefonia)
Justificativa: Aparelho de telefonia celular com múltiplas funções

Produto: "Televisão LED 55 polegadas LG"
NCM: 8528.72.10 (Aparelhos receptores de televisão)
CEST: 01.003.00 (Equipamentos de áudio e vídeo)
Justificativa: Aparelho receptor de sinais de televisão
"""

        prompt = f"""Você é um especialista em classificação fiscal brasileira NCM e CEST.

{exemplos}

TAREFA: Classifique o produto abaixo seguindo o padrão dos exemplos:

Produto: "{descricao}"

Responda APENAS no formato JSON:
{{
    "ncm": "código NCM sugerido (8 dígitos)",
    "ncm_confianca": número de 0 a 1,
    "cest": "código CEST sugerido ou null",
    "cest_confianca": número de 0 a 1,
    "justificativa": "explicação técnica da classificação",
    "categorias": ["categoria1", "categoria2"],
    "palavras_chave": ["palavra1", "palavra2", "palavra3"]
}}

IMPORTANTE:
- Use códigos NCM reais de 8 dígitos
- CEST pode ser null se não aplicável
- Confiança: 0.8+ = alta, 0.5-0.8 = média, <0.5 = baixa
- Justificativa técnica baseada na nomenclatura oficial
"""

        return prompt

    def parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Processa resposta do LLM e extrai classificação"""
        try:
            # Tentar extrair JSON da resposta
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception:
            pass

        # Fallback: parsing manual se JSON falhar
        result = {
            "ncm": "0000.00.00",
            "ncm_confianca": 0.1,
            "cest": None,
            "cest_confianca": 0.1,
            "justificativa": "Erro ao processar resposta do modelo",
            "categorias": ["indefinida"],
            "palavras_chave": [],
        }

        # Tentar extrair NCM
        ncm_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", response)
        if ncm_match:
            result["ncm"] = ncm_match.group()
            result["ncm_confianca"] = 0.6

        # Tentar extrair CEST
        cest_match = re.search(r"(\d{2}\.\d{3}\.\d{2})", response)
        if cest_match:
            result["cest"] = cest_match.group()
            result["cest_confianca"] = 0.6

        return result

    def classify_product(self, produto_id: str, descricao: str) -> ClassificationResult:
        """Classifica um produto usando IA local"""
        start_time = time.time()

        # Verificar conexão com Ollama
        if not self.check_ollama_connection():
            logger.error("Ollama não está rodando!")
            return ClassificationResult(
                produto_id=produto_id,
                descricao=descricao,
                ncm_sugerido="0000.00.00",
                ncm_confianca=0.0,
                cest_sugerido=None,
                cest_confianca=0.0,
                justificativa="Ollama não disponível",
                modelo_usado="none",
                tempo_processamento=0.0,
                categorias_identificadas=["erro"],
                palavras_chave=[],
            )

        # Criar prompt de classificação
        prompt = self.create_classification_prompt(descricao)

        # Consultar modelo
        modelo_usado = self.config.modelo_principal
        response = self.query_ollama(prompt, modelo_usado)

        if not response:
            modelo_usado = self.config.modelo_backup
            response = self.query_ollama(prompt, modelo_usado)

        if not response:
            logger.error("Falha ao obter resposta do modelo")
            return ClassificationResult(
                produto_id=produto_id,
                descricao=descricao,
                ncm_sugerido="0000.00.00",
                ncm_confianca=0.0,
                cest_sugerido=None,
                cest_confianca=0.0,
                justificativa="Falha na consulta ao modelo",
                modelo_usado="error",
                tempo_processamento=time.time() - start_time,
                categorias_identificadas=["erro"],
                palavras_chave=[],
            )

        # Processar resposta
        classification = self.parse_classification_response(response)

        tempo_processamento = time.time() - start_time

        return ClassificationResult(
            produto_id=produto_id,
            descricao=descricao,
            ncm_sugerido=classification.get("ncm", "0000.00.00"),
            ncm_confianca=float(classification.get("ncm_confianca", 0.0)),
            cest_sugerido=classification.get("cest"),
            cest_confianca=float(classification.get("cest_confianca", 0.0)),
            justificativa=classification.get(
                "justificativa", "Classificação automática"
            ),
            modelo_usado=modelo_usado,
            tempo_processamento=tempo_processamento,
            categorias_identificadas=classification.get("categorias", []),
            palavras_chave=classification.get("palavras_chave", []),
        )

    def batch_classify(
        self, produtos: List[Dict[str, str]]
    ) -> List[ClassificationResult]:
        """Classifica múltiplos produtos em lote"""
        results = []
        total = len(produtos)

        logger.info(f"Iniciando classificação em lote de {total} produtos")

        for i, produto in enumerate(produtos, 1):
            logger.info(
                f"Classificando produto {i}/{total}: {produto.get('descricao', '')[:50]}..."
            )

            result = self.classify_product(
                produto.get("produto_id", f"prod_{i}"), produto.get("descricao", "")
            )

            results.append(result)

            # Log do resultado
            logger.info(
                f"  → NCM: {result.ncm_sugerido} (conf: {result.ncm_confianca:.2f})"
            )
            if result.cest_sugerido:
                logger.info(
                    f"  → CEST: {result.cest_sugerido} (conf: {result.cest_confianca:.2f})"
                )

        return results

    def export_results(self, results: List[ClassificationResult], filename: str = None):
        """Exporta resultados para JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/processed/classificacao_ia_local_{timestamp}.json"

        # Converter para dicionários
        results_dict = [asdict(result) for result in results]

        # Criar diretório se não existir
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        # Salvar arquivo
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_produtos": len(results),
                    "modelo_config": asdict(self.config),
                    "resultados": results_dict,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"Resultados exportados para: {filename}")
        return filename


def install_ollama_models():
    """Instala modelos recomendados no Ollama"""
    config = OllamaConfig()
    classifier = LocalLLMClassifier(config)

    modelos_recomendados = [
        "llama3.1:8b",  # Modelo principal (mais preciso)
        "llama2:7b",  # Modelo backup (mais rápido)
        "mistral:7b",  # Alternativa em português
        "codellama:7b",  # Para parsing de códigos
    ]

    print("🤖 Instalando modelos LLM locais via Ollama...")
    print("=" * 60)

    for modelo in modelos_recomendados:
        print(f"\n📦 Instalando {modelo}...")
        success = classifier.ensure_model_available(modelo)
        if success:
            print(f"✅ {modelo} instalado com sucesso!")
        else:
            print(f"❌ Falha ao instalar {modelo}")

    print("\n🎉 Instalação concluída!")
    print(f"📋 Modelos disponíveis: {classifier.get_available_models()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sistema de IA Local com Ollama")
    parser.add_argument(
        "--install-models", action="store_true", help="Instalar modelos recomendados"
    )
    parser.add_argument("--test", action="store_true", help="Executar teste rápido")
    parser.add_argument("--produto", help="Classificar produto específico")

    args = parser.parse_args()

    if args.install_models:
        install_ollama_models()
    elif args.test:
        # Teste rápido
        classifier = LocalLLMClassifier()

        produtos_teste = [
            {"produto_id": "1", "descricao": "Notebook Dell Inspiron 15"},
            {"produto_id": "2", "descricao": "Smartphone Samsung Galaxy"},
            {"produto_id": "3", "descricao": "Televisão LED 55 polegadas"},
        ]

        print("🧪 Teste do Sistema de IA Local")
        print("=" * 50)

        for produto in produtos_teste:
            result = classifier.classify_product(
                produto["produto_id"], produto["descricao"]
            )
            print(f"\n📱 {produto['descricao']}")
            print(f"   NCM: {result.ncm_sugerido} (conf: {result.ncm_confianca:.2f})")
            print(
                f"   CEST: {result.cest_sugerido} (conf: {result.cest_confianca:.2f})"
            )
            print(f"   Modelo: {result.modelo_usado}")
            print(f"   Tempo: {result.tempo_processamento:.2f}s")

    elif args.produto:
        classifier = LocalLLMClassifier()
        result = classifier.classify_product("teste", args.produto)
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))

    else:
        print("Use --help para ver as opções disponíveis")
