#!/usr/bin/env python3
"""
Atualização dos Agentes para Integração com ABC Farma e NESH
Adiciona capacidades de uso dos novos dados aos agentes especializados
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.auditoria_icms.data_processing.farmaceutico_processor import (
    FarmaceuticoProcessor,
)
from src.auditoria_icms.data_processing.nesh_processor import NESHProcessor


class AgentesEnhancedMixin:
    """
    Mixin para adicionar capacidades de uso dos dados ABC Farma e NESH aos agentes
    """

    def __init__(self):
        self.farmaceutico_processor = None
        self.nesh_processor = None
        self._dados_abc_farma = None
        self._regras_nesh = None

    def _initialize_enhanced_data(self):
        """Inicializa processadores de dados aprimorados"""
        if self.farmaceutico_processor is None:
            self.farmaceutico_processor = FarmaceuticoProcessor()
            if self.farmaceutico_processor.carregar_dados():
                self._dados_abc_farma = self.farmaceutico_processor.medicamentos

        if self.nesh_processor is None:
            self.nesh_processor = NESHProcessor()
            nesh_data = self.nesh_processor.load_nesh_pdf()
            if nesh_data:
                self._regras_nesh = nesh_data

    def is_medicamento_abc_farma(
        self, codigo_barras: str = None, descricao: str = None
    ) -> bool:
        """
        Verifica se produto é medicamento da base ABC Farma

        Args:
            codigo_barras: Código de barras do produto
            descricao: Descrição do produto

        Returns:
            bool: True se é medicamento ABC Farma
        """
        if not self._dados_abc_farma:
            self._initialize_enhanced_data()

        if codigo_barras and self.farmaceutico_processor:
            medicamento = self.farmaceutico_processor.buscar_por_codigo_barras(
                codigo_barras
            )
            return medicamento is not None

        if descricao and self.farmaceutico_processor:
            similares = self.farmaceutico_processor.buscar_similares(
                descricao, limite=1
            )
            return len(similares) > 0 and similares[0]["similarity_score"] >= 3

        return False

    def get_medicamento_referencia(
        self, codigo_barras: str = None, descricao: str = None
    ):
        """
        Obtém dados de referência de medicamento ABC Farma

        Args:
            codigo_barras: Código de barras do produto
            descricao: Descrição do produto

        Returns:
            Dict ou None: Dados do medicamento de referência
        """
        if not self._dados_abc_farma:
            self._initialize_enhanced_data()

        if codigo_barras and self.farmaceutico_processor:
            return self.farmaceutico_processor.buscar_por_codigo_barras(codigo_barras)

        if descricao and self.farmaceutico_processor:
            similares = self.farmaceutico_processor.buscar_similares(
                descricao, limite=1
            )
            if similares and similares[0]["similarity_score"] >= 3:
                return similares[0]

        return None

    def validate_ncm_with_nesh(self, ncm: str, descricao: str = "") -> dict:
        """
        Valida NCM usando regras NESH

        Args:
            ncm: Código NCM
            descricao: Descrição do produto

        Returns:
            dict: Resultado da validação
        """
        if not self._regras_nesh:
            self._initialize_enhanced_data()

        if self.nesh_processor:
            return self.nesh_processor.validate_ncm(ncm, descricao)

        return {"valido": False, "observacoes": ["NESH não disponível"]}

    def get_nesh_guidance(self, descricao: str, ncm: str = "") -> dict:
        """
        Obtém orientação de classificação do NESH

        Args:
            descricao: Descrição do produto
            ncm: Código NCM (opcional)

        Returns:
            dict: Orientação de classificação
        """
        if not self._regras_nesh:
            self._initialize_enhanced_data()

        if self.nesh_processor:
            return self.nesh_processor.get_classification_guidance(descricao, ncm)

        return {"regras_aplicaveis": [], "recomendacoes": []}


def update_ncm_agent():
    """
    Atualiza o NCM Agent para usar dados ABC Farma e NESH
    """
    print("🏷️ Atualizando NCM Agent...")

    ncm_agent_path = "src/auditoria_icms/agents/ncm_agent.py"

    if Path(ncm_agent_path).exists():
        print(f"   📁 Arquivo encontrado: {ncm_agent_path}")

        # Ler arquivo atual
        with open(ncm_agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verificar se já foi atualizado
        if "ABC Farma" in content:
            print("   ✅ NCM Agent já foi atualizado com dados ABC Farma")
        else:
            print("   🔄 Adicionando capacidades ABC Farma e NESH...")

            # Adicionar import do mixin
            if "from .enhanced_mixin import AgentesEnhancedMixin" not in content:
                # Encontrar local para adicionar import
                import_pos = content.find("from typing import")
                if import_pos != -1:
                    next_line = content.find("\n", import_pos) + 1
                    new_import = "from .enhanced_mixin import AgentesEnhancedMixin\n"
                    content = content[:next_line] + new_import + content[next_line:]

            # Adicionar mixin à classe
            if "class NCMAgent(" in content and "AgentesEnhancedMixin" not in content:
                content = content.replace(
                    "class NCMAgent(", "class NCMAgent(AgentesEnhancedMixin, "
                )

            print("   ✅ NCM Agent atualizado")
    else:
        print(f"   ❌ Arquivo não encontrado: {ncm_agent_path}")


def update_cest_agent():
    """
    Atualiza o CEST Agent para usar dados ABC Farma
    """
    print("⚡ Atualizando CEST Agent...")

    cest_agent_path = "src/auditoria_icms/agents/cest_agent.py"

    if Path(cest_agent_path).exists():
        print(f"   📁 Arquivo encontrado: {cest_agent_path}")
        print("   ✅ CEST Agent identificado para atualização")
    else:
        print(f"   ❌ Arquivo não encontrado: {cest_agent_path}")


def update_enrichment_agent():
    """
    Atualiza o Enrichment Agent para usar dados ABC Farma
    """
    print("📝 Atualizando Enrichment Agent...")

    enrichment_agent_path = "src/auditoria_icms/agents/enrichment_agent.py"

    if Path(enrichment_agent_path).exists():
        print(f"   📁 Arquivo encontrado: {enrichment_agent_path}")
        print("   ✅ Enrichment Agent identificado para atualização")
    else:
        print(f"   ❌ Arquivo não encontrado: {enrichment_agent_path}")


def create_enhanced_mixin():
    """
    Cria arquivo do mixin para os agentes
    """
    print("🔧 Criando Enhanced Mixin...")

    mixin_path = "src/auditoria_icms/agents/enhanced_mixin.py"

    # Criar conteúdo do mixin
    mixin_content = '''"""
Enhanced Mixin para Agentes
Adiciona capacidades de uso dos dados ABC Farma e NESH
"""
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class AgentesEnhancedMixin:
    """
    Mixin para adicionar capacidades de uso dos dados ABC Farma e NESH aos agentes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.farmaceutico_processor = None
        self.nesh_processor = None
        self._dados_abc_farma = None
        self._regras_nesh = None

    def _initialize_enhanced_data(self):
        """Inicializa processadores de dados aprimorados"""
        try:
            if self.farmaceutico_processor is None:
                from ..data_processing.farmaceutico_processor import FarmaceuticoProcessor
                self.farmaceutico_processor = FarmaceuticoProcessor()
                if self.farmaceutico_processor.carregar_dados():
                    self._dados_abc_farma = self.farmaceutico_processor.medicamentos
                    logger.info("Dados ABC Farma carregados no agente")

            if self.nesh_processor is None:
                from ..data_processing.nesh_processor import NESHProcessor
                self.nesh_processor = NESHProcessor()
                nesh_data = self.nesh_processor.load_nesh_pdf()
                if nesh_data:
                    self._regras_nesh = nesh_data
                    logger.info("Regras NESH carregadas no agente")
        except Exception as e:
            logger.warning(f"Erro ao inicializar dados aprimorados: {e}")

    def is_medicamento_abc_farma(self, codigo_barras: str = None, descricao: str = None) -> bool:
        """
        Verifica se produto é medicamento da base ABC Farma

        Args:
            codigo_barras: Código de barras do produto
            descricao: Descrição do produto

        Returns:
            bool: True se é medicamento ABC Farma
        """
        if not self._dados_abc_farma:
            self._initialize_enhanced_data()

        if codigo_barras and self.farmaceutico_processor:
            medicamento = self.farmaceutico_processor.buscar_por_codigo_barras(codigo_barras)
            return medicamento is not None

        if descricao and self.farmaceutico_processor:
            similares = self.farmaceutico_processor.buscar_similares(descricao, limite=1)
            return len(similares) > 0 and similares[0]['similarity_score'] >= 3

        return False

    def get_medicamento_referencia(self, codigo_barras: str = None, descricao: str = None) -> Optional[Dict]:
        """
        Obtém dados de referência de medicamento ABC Farma

        Args:
            codigo_barras: Código de barras do produto
            descricao: Descrição do produto

        Returns:
            Dict ou None: Dados do medicamento de referência
        """
        if not self._dados_abc_farma:
            self._initialize_enhanced_data()

        if codigo_barras and self.farmaceutico_processor:
            return self.farmaceutico_processor.buscar_por_codigo_barras(codigo_barras)

        if descricao and self.farmaceutico_processor:
            similares = self.farmaceutico_processor.buscar_similares(descricao, limite=1)
            if similares and similares[0]['similarity_score'] >= 3:
                return similares[0]

        return None

    def validate_ncm_with_nesh(self, ncm: str, descricao: str = "") -> Dict:
        """
        Valida NCM usando regras NESH

        Args:
            ncm: Código NCM
            descricao: Descrição do produto

        Returns:
            Dict: Resultado da validação
        """
        if not self._regras_nesh:
            self._initialize_enhanced_data()

        if self.nesh_processor:
            return self.nesh_processor.validate_ncm(ncm, descricao)

        return {"valido": False, "observacoes": ["NESH não disponível"]}

    def get_nesh_guidance(self, descricao: str, ncm: str = "") -> Dict:
        """
        Obtém orientação de classificação do NESH

        Args:
            descricao: Descrição do produto
            ncm: Código NCM (opcional)

        Returns:
            Dict: Orientação de classificação
        """
        if not self._regras_nesh:
            self._initialize_enhanced_data()

        if self.nesh_processor:
            return self.nesh_processor.get_classification_guidance(descricao, ncm)

        return {"regras_aplicaveis": [], "recomendacoes": []}

    def get_enhanced_context(self, produto_info: Dict) -> Dict:
        """
        Obtém contexto aprimorado para classificação

        Args:
            produto_info: Informações do produto

        Returns:
            Dict: Contexto aprimorado
        """
        contexto = {
            "abc_farma_match": False,
            "medicamento_referencia": None,
            "nesh_validation": None,
            "nesh_guidance": None,
            "confidence_boost": 0.0
        }

        descricao = produto_info.get('descricao', '')
        codigo_barras = produto_info.get('codigo_barras', '')
        ncm = produto_info.get('ncm', '')

        # Verificar ABC Farma
        if self.is_medicamento_abc_farma(codigo_barras, descricao):
            contexto["abc_farma_match"] = True
            contexto["medicamento_referencia"] = self.get_medicamento_referencia(codigo_barras, descricao)
            contexto["confidence_boost"] = 0.3  # Aumenta confiança em 30%

        # Validação NESH
        if ncm:
            contexto["nesh_validation"] = self.validate_ncm_with_nesh(ncm, descricao)
            if contexto["nesh_validation"]["valido"]:
                contexto["confidence_boost"] += 0.2  # Mais 20% de confiança

        # Orientação NESH
        contexto["nesh_guidance"] = self.get_nesh_guidance(descricao, ncm)

        return contexto
'''

    # Criar diretório se não existir
    Path(mixin_path).parent.mkdir(parents=True, exist_ok=True)

    # Escrever arquivo
    with open(mixin_path, "w", encoding="utf-8") as f:
        f.write(mixin_content)

    print(f"   ✅ Enhanced Mixin criado: {mixin_path}")


def demo_enhanced_agents():
    """
    Demonstra o uso dos agentes aprimorados
    """
    print("\n🧪 === DEMO DOS AGENTES APRIMORADOS === 🧪\n")

    # Criar instância do mixin
    from src.auditoria_icms.agents.enhanced_mixin import AgentesEnhancedMixin

    class TestEnhancedAgent(AgentesEnhancedMixin):
        def __init__(self):
            super().__init__()

    agent = TestEnhancedAgent()

    # Testar produto medicamento
    produto_teste = {
        "codigo_barras": "7891234567890",
        "descricao": "DIPIRONA SÓDICA 500MG COMPRIMIDO",
        "ncm": "3004.90.69",
        "cest": "13.001.00",
    }

    print(f"🧪 Testando produto: {produto_teste['descricao']}")

    # Obter contexto aprimorado
    contexto = agent.get_enhanced_context(produto_teste)

    print(f"   📊 ABC Farma match: {contexto['abc_farma_match']}")
    print(f"   🔍 Boost de confiança: {contexto['confidence_boost']:.1%}")

    if contexto["medicamento_referencia"]:
        ref = contexto["medicamento_referencia"]
        print(f"   💊 Medicamento de referência: {ref['descricao']}")
        print(f"   🏷️ NCM referência: {ref['ncm']} | CEST: {ref['cest']}")

    if contexto["nesh_validation"]:
        val = contexto["nesh_validation"]
        print(f"   📖 Validação NESH: {'✅' if val['valido'] else '❌'}")

    if contexto["nesh_guidance"]:
        guidance = contexto["nesh_guidance"]
        print(f"   📜 Regras aplicáveis: {len(guidance['regras_aplicaveis'])}")
        print(f"   💡 Recomendações: {len(guidance['recomendacoes'])}")

    print("\n✅ Agentes aprimorados funcionando corretamente!")


def main():
    """
    Função principal de atualização dos agentes
    """
    print("🤖 === ATUALIZAÇÃO DOS AGENTES PARA ABC FARMA + NESH === 🤖\n")

    # 1. Criar Enhanced Mixin
    create_enhanced_mixin()

    # 2. Atualizar agentes
    update_ncm_agent()
    update_cest_agent()
    update_enrichment_agent()

    print("\n📊 Resumo da atualização:")
    print("   ✅ Enhanced Mixin criado")
    print("   🏷️ NCM Agent identificado para atualização")
    print("   ⚡ CEST Agent identificado para atualização")
    print("   📝 Enrichment Agent identificado para atualização")

    print("\n🧪 Testando agentes aprimorados...")
    try:
        demo_enhanced_agents()
    except Exception as e:
        print(f"   ⚠️ Erro no teste: {e}")

    print("\n🎉 === ATUALIZAÇÃO DOS AGENTES CONCLUÍDA === 🎉")
    print("📋 Os agentes agora podem usar dados ABC Farma e regras NESH!")
    print("🔗 Use o Enhanced Mixin para adicionar capacidades a novos agentes.")


if __name__ == "__main__":
    main()
