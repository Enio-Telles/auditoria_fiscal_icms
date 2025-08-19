"""
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
